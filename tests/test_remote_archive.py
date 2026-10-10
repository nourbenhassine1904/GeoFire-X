"""Tests for the entry-parsing/extraction logic in geofirex.remote_archive,
using a small LOCAL zip (no network) so they run fast and offline. HttpRangeFile
itself (the network-specific Range-request logic) was validated manually
against the live Zenodo server - see reports/DATA_AUDIT.md §1.
"""

import zipfile
from pathlib import Path

from geofirex.remote_archive import extract_events, list_real_events


def _build_local_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("2018/fire_111/2018-05-03.tif", b"fake-day-1")
        zf.writestr("2018/fire_111/2018-05-04.tif", b"fake-day-2")
        zf.writestr("2019/fire_222/2019-07-01.tif", b"fake-day-3")
        zf.writestr("2018/fire_111/", b"")  # a folder entry, must be ignored
        zf.writestr("README.txt", b"not an event file")  # unexpected top-level file


def test_list_real_events_parses_year_fire_date_layout(tmp_path: Path):
    zip_path = tmp_path / "fake.zip"
    _build_local_zip(zip_path)

    with zipfile.ZipFile(zip_path) as zf:
        events = list_real_events(zf)

    assert set(events.keys()) == {"2018/fire_111", "2019/fire_222"}
    assert events["2018/fire_111"] == ["2018-05-03.tif", "2018-05-04.tif"]
    assert events["2019/fire_222"] == ["2019-07-01.tif"]


def test_extract_events_writes_only_requested_events(tmp_path: Path):
    zip_path = tmp_path / "fake.zip"
    _build_local_zip(zip_path)
    dest = tmp_path / "extracted"

    with zipfile.ZipFile(zip_path) as zf:
        written = extract_events(zf, ["2019/fire_222"], dest)

    assert len(written) == 1
    out_file = dest / "2019" / "fire_222" / "2019-07-01.tif"
    assert out_file in written
    assert out_file.read_bytes() == b"fake-day-3"
    # The other event must not have been extracted.
    assert not (dest / "2018").exists()
