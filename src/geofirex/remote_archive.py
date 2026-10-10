"""Read the official WildfireSpreadTS.zip (Zenodo 8006177, 48.36 GB) remotely via
HTTP Range requests, without downloading the full archive.

The Zenodo CDN advertises `Accept-Ranges: bytes` (verified manually). Python's
`zipfile` only needs an object with `seek()`/`tell()`/`read()` to parse the
central directory and open individual entries — it never requires the whole
file. This lets us: (1) list the real on-disk structure of the dataset for free
(a few hundred KB of central-directory metadata), and (2) extract a handful of
real events on demand, paying only for the bytes of those entries.

Stdlib only (urllib + zipfile) — no new dependency.
"""

from __future__ import annotations

import logging
import time
import urllib.request
import zipfile
from pathlib import Path

logger = logging.getLogger(__name__)

ZENODO_RECORD_ID = "8006177"
ARCHIVE_URL = (
    f"https://zenodo.org/api/records/{ZENODO_RECORD_ID}/files/WildfireSpreadTS.zip/content"
)


class HttpRangeFile:
    """Minimal seek/read file-like object backed by HTTP Range requests.

    The Zenodo CDN has been observed returning transient 502/504 errors under
    load, so every request is retried with backoff rather than failing fast.
    """

    def __init__(self, url: str, total_size: int, timeout: int = 90, retries: int = 5) -> None:
        self.url = url
        self.size = total_size
        self.pos = 0
        self.timeout = timeout
        self.retries = retries
        self.bytes_fetched = 0  # for honest reporting of what was actually downloaded

    def seek(self, offset: int, whence: int = 0) -> int:
        if whence == 0:
            self.pos = offset
        elif whence == 1:
            self.pos += offset
        elif whence == 2:
            self.pos = self.size + offset
        return self.pos

    def tell(self) -> int:
        return self.pos

    def seekable(self) -> bool:
        return True

    def read(self, n: int = -1) -> bytes:
        if n < 0:
            end = self.size - 1
        else:
            end = min(self.pos + n, self.size) - 1
        if self.pos > end:
            return b""
        req = urllib.request.Request(self.url, headers={"Range": f"bytes={self.pos}-{end}"})
        with _fetch_with_retry(req, timeout=self.timeout, retries=self.retries) as resp:
            data = resp.read()
        self.pos += len(data)
        self.bytes_fetched += len(data)
        return data


def _fetch_with_retry(req: urllib.request.Request, timeout: int = 90, retries: int = 5):
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except Exception as e:  # noqa: BLE001 - retry any transient error (502/504 observed)
            last_err = e
            logger.warning("request failed (attempt %d/%d): %s", attempt + 1, retries, e)
            time.sleep(5)
    raise RuntimeError(f"Giving up after {retries} attempts") from last_err


def get_remote_size(url: str = ARCHIVE_URL, timeout: int = 90, retries: int = 5) -> int:
    """Return the exact size of a remote file via a 1-byte Range probe."""
    req = urllib.request.Request(url, headers={"Range": "bytes=0-0"})
    with _fetch_with_retry(req, timeout=timeout, retries=retries) as resp:
        content_range = resp.headers.get("Content-Range", "")
    return int(content_range.split("/")[-1])


def open_remote_zip(url: str = ARCHIVE_URL) -> tuple[zipfile.ZipFile, HttpRangeFile]:
    """Open the remote archive's central directory without downloading its body."""
    size = get_remote_size(url)
    f = HttpRangeFile(url, size)
    return zipfile.ZipFile(f), f


def list_real_events(zf: zipfile.ZipFile) -> dict[str, list[str]]:
    """Map event_id ("<year>/fire_<id>") -> sorted list of day filenames (*.tif)."""
    events: dict[str, list[str]] = {}
    for name in zf.namelist():
        if name.endswith("/") or not name.endswith(".tif"):
            continue
        parts = name.split("/")
        if len(parts) != 3:
            continue  # unexpected layout - do not silently misclassify
        year, fire_dir, filename = parts
        event_id = f"{year}/{fire_dir}"
        events.setdefault(event_id, []).append(filename)
    for v in events.values():
        v.sort()
    return events


def extract_events(
    zf: zipfile.ZipFile,
    event_ids: list[str],
    dest_dir: Path,
) -> list[Path]:
    """Decompress every .tif belonging to the given events into dest_dir,
    preserving the official <year>/fire_<id>/<date>.tif layout. Only the bytes
    of these specific entries are fetched from the remote archive."""
    dest_dir = Path(dest_dir)
    written = []
    wanted = set(event_ids)
    for name in zf.namelist():
        if name.endswith("/") or not name.endswith(".tif"):
            continue
        parts = name.split("/")
        if len(parts) != 3:
            continue
        year, fire_dir, filename = parts
        event_id = f"{year}/{fire_dir}"
        if event_id not in wanted:
            continue
        out_path = dest_dir / year / fire_dir / filename
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(name) as src, out_path.open("wb") as dst:
            dst.write(src.read())
        written.append(out_path)
    return written
