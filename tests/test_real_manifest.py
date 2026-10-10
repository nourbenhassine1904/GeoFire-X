"""Tests use small artificial GeoTIFFs mimicking the REAL 23-band raw layout
(not the 40-channel synthetic fixtures) - no dependency on the full download.
"""

from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

from geofirex.real_manifest import build_real_manifest

REAL_RAW_BAND_NAMES = [
    "M11", "I2", "I1", "NDVI_last", "EVI2_last", "total precipitation",
    "wind speed", "wind direction", "minimum temperature", "maximum temperature",
    "energy release component", "specific humidity", "slope", "aspect", "elevation",
    "pdsi", "LC_Type1", "total_precipitation_surface_sum", "forecast wind speed",
    "forecast wind direction", "forecast temperature", "forecast specific humidity",
    "active fire",
]


def _write_fake_real_day(path: Path, day: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = np.zeros((23, 8, 8), dtype="float32")
    with rasterio.open(
        path, "w", driver="GTiff", height=8, width=8, count=23, dtype="float32",
        crs="EPSG:32610", transform=from_origin(0.0, 0.0, 375.0, 375.0),
    ) as dst:
        dst.write(data)
        dst.descriptions = REAL_RAW_BAND_NAMES


def test_build_real_manifest_reads_actual_band_count(tmp_path: Path):
    data_dir = tmp_path / "real_sample"
    _write_fake_real_day(data_dir / "2018" / "fire_99999999" / "2018-05-03.tif", "2018-05-03")
    _write_fake_real_day(data_dir / "2018" / "fire_99999999" / "2018-05-05.tif", "2018-05-05")  # gap

    rows = build_real_manifest(data_dir)
    assert len(rows) == 2
    assert all(r["num_channels"] == 23 for r in rows)  # real raw layout, not 40
    assert rows[0]["event_id"] == "2018/fire_99999999"
    assert rows[0]["band_names"].split(";")[-1] == "active fire"

    gap_row = rows[1]
    assert gap_row["gap_days_since_previous_observation"] == 2  # 05-03 -> 05-05

    # Fields we cannot determine from the files are documented as empty, not guessed.
    assert rows[0]["fire_display_name"] == ""
    assert rows[0]["ignition_coordinates"] == ""


def test_build_real_manifest_empty_dir_returns_no_rows(tmp_path: Path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    rows = build_real_manifest(empty_dir)
    assert rows == []
