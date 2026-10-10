"""Extract a small, deterministic sample of REAL WildfireSpreadTS events from
the official Zenodo archive, without downloading the full 48.36 GB file.

Only the compressed bytes of the chosen events' .tif files are fetched (a real
event is roughly 20-90 MB for a handful of events total - see the printed
report). This is a deliberate choice to get genuine, verified data for the
Phase 2 audit while respecting the project rule against downloading tens of
GB without explicit team agreement.

Usage:
    python scripts/download_real_sample.py \\
        --dest data/raw/WildfireSpreadTS/real_sample \\
        --num_events 5 --seed 42
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path

from geofirex.remote_archive import extract_events, list_real_events, open_remote_zip


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", required=True)
    parser.add_argument("--num_events", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    dest_dir = Path(args.dest)
    dest_dir.mkdir(parents=True, exist_ok=True)

    zf, f = open_remote_zip()
    events = list_real_events(zf)
    print(f"Real events available in the official archive: {len(events)}")

    ordered_ids = sorted(events.keys())  # sort first so sampling is reproducible
    rng = random.Random(args.seed)
    chosen = sorted(rng.sample(ordered_ids, k=min(args.num_events, len(ordered_ids))))
    print(f"Selected {len(chosen)} event(s) with seed={args.seed}: {chosen}")

    already = [c for c in chosen if (dest_dir / c).is_dir() and any((dest_dir / c).glob("*.tif"))]
    to_fetch = [c for c in chosen if c not in already]
    if already:
        print(f"Already present locally, skipping: {already}")

    written = extract_events(zf, to_fetch, dest_dir) if to_fetch else []

    print(f"Wrote {len(written)} real .tif file(s) to {dest_dir}")
    print(f"Bytes actually fetched from Zenodo this run: {f.bytes_fetched:,} "
          f"({f.bytes_fetched / 1e6:.2f} MB)")
    print("No part of the full 48.36 GB archive was downloaded.")


if __name__ == "__main__":
    main()
