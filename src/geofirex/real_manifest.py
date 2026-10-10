"""Build an enriched manifest for the REAL WildfireSpreadTS sample.

Deliberately separate from geofirex.manifest (which stays fast and
format-agnostic for the synthetic pipeline): this module reads each GeoTIFF's
header with rasterio to record real channel count, shape and dtype, because
Phase F of the dataset audit requires that metadata and we must not assume it
matches the synthetic fixtures or the paper's post-preprocessing figures.

Fields we cannot determine from the files themselves (e.g. a human-readable
fire name, precise ignition coordinates) are left empty rather than guessed.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path

import rasterio

from geofirex.io import list_event_days, list_events


def build_real_manifest(data_dir: Path) -> list[dict]:
    """One row per real day file, with metadata read directly from the GeoTIFF."""
    rows = []
    for event_dir in list_events(data_dir):
        year = event_dir.parent.name
        fire_id = event_dir.name  # e.g. "fire_21748813" - official numeric id, not a descriptive name
        event_id = f"{year}/{fire_id}"
        days = list_event_days(event_dir)
        dates_sorted = [d.date for d in days]

        prev_date = None
        for day in days:
            gap_days = None
            try:
                cur = dt.date.fromisoformat(day.date)
                if prev_date is not None:
                    gap_days = (cur - prev_date).days
                prev_date = cur
            except ValueError:
                pass  # filename not a valid ISO date - leave gap_days unset

            with rasterio.open(day.path) as ds:
                num_channels = ds.count
                height, width = ds.height, ds.width
                dtype = ds.dtypes[0]
                crs = str(ds.crs) if ds.crs else ""
                band_names = list(ds.descriptions) if ds.descriptions else []

            rows.append(
                {
                    "event_id": event_id,
                    "year": year,
                    "fire_id": fire_id,
                    "date": day.date,
                    "relative_path": day.path.as_posix(),
                    "observation_type": "daily_geotiff",
                    "num_channels": num_channels,
                    "height": height,
                    "width": width,
                    "dtype": dtype,
                    "crs": crs,
                    "band_names": ";".join(band_names) if band_names else "",
                    "gap_days_since_previous_observation": gap_days if gap_days is not None else "",
                    # Not determinable from the files themselves - documented as absent,
                    # not guessed (Phase F instruction: "ne remplis pas artificiellement").
                    "fire_display_name": "",
                    "ignition_coordinates": "",
                }
            )
    return rows


FIELDNAMES = [
    "event_id", "year", "fire_id", "date", "relative_path", "observation_type",
    "num_channels", "height", "width", "dtype", "crs", "band_names",
    "gap_days_since_previous_observation", "fire_display_name", "ignition_coordinates",
]


def save_real_manifest(rows: list[dict], out_path: Path) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data_dir", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    rows = build_real_manifest(Path(args.data_dir))
    if not rows:
        raise SystemExit(f"No real GeoTIFF files found under {args.data_dir}.")
    save_real_manifest(rows, Path(args.out))
    n_events = len({r["event_id"] for r in rows})
    print(f"Real manifest: {len(rows)} day-rows across {n_events} event(s) -> {args.out}")


if __name__ == "__main__":
    main()
