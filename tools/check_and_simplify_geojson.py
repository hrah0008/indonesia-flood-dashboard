"""
tools/check_and_simplify_geojson.py
====================================
Diagnose and (optionally) simplify your regencies.geojson.

Run from the project root:
    python tools/check_and_simplify_geojson.py

What it does:
  1. Reports file size, feature count, coordinate count
  2. Tests data ↔ geojson key match rate
  3. Reports geometry validity
  4. If the file is too big or too detailed for web rendering,
     writes a simplified version next to it:
       public/data/geo/regencies.geojson           (original, untouched)
       public/data/geo/regencies_simplified.geojson  (NEW — use this)

If a simplified version is created, point your dashboard at it by editing
lib/data_flood.py:

    def load_regencies_geojson() -> dict:
        return _read_json(str(_GEO_DIR / "regencies_simplified.geojson"))

Requirements:
    pip install geopandas shapely
"""

import json
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
GEO_PATH     = PROJECT_ROOT / "public" / "data" / "geo" / "regencies.geojson"
OUT_PATH     = PROJECT_ROOT / "public" / "data" / "geo" / "regencies_simplified.geojson"
PARQUET_PATH = PROJECT_ROOT / "public" / "data" / "flood" / "national" / "regency_table.parquet"


def fmt_bytes(n: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.2f} {unit}"
        n /= 1024
    return f"{n:.2f} TB"


def count_coords(coords) -> int:
    """Recursively count [lon, lat] pairs in any GeoJSON coordinate structure."""
    if isinstance(coords, list):
        if coords and isinstance(coords[0], (int, float)):
            return 1
        return sum(count_coords(c) for c in coords)
    return 0


# ════════════════════════════════════════════════════════════════════
# Step 1 — File on disk
# ════════════════════════════════════════════════════════════════════
print("=" * 60)
print("STEP 1 — File inspection")
print("=" * 60)

if not GEO_PATH.exists():
    print(f"❌ FILE NOT FOUND: {GEO_PATH}")
    print("   Run nb11 (build_dashboard_geo) and copy web/regencies.geojson")
    print("   to public/data/geo/regencies.geojson")
    sys.exit(1)

size_bytes = GEO_PATH.stat().st_size
size_mb = size_bytes / (1024 * 1024)
print(f"📂 Path: {GEO_PATH}")
print(f"📦 Size: {fmt_bytes(size_bytes)}")

if size_mb > 20:
    print(f"🚨 TOO BIG — should be 2-5 MB for web rendering")
elif size_mb > 10:
    print(f"⚠️  Larger than ideal (2-5 MB). Slower but workable.")
elif size_mb < 0.5:
    print(f"⚠️  Suspiciously small — verify it has 514 regencies")
else:
    print(f"✅ Size looks fine")


# ════════════════════════════════════════════════════════════════════
# Step 2 — Load and parse
# ════════════════════════════════════════════════════════════════════
print()
print("=" * 60)
print("STEP 2 — Load + parse timing")
print("=" * 60)

t0 = time.time()
with open(GEO_PATH, "r", encoding="utf-8") as f:
    raw = f.read()
print(f"⏱️  Disk read:   {(time.time() - t0) * 1000:.0f} ms")

t0 = time.time()
geo = json.loads(raw)
print(f"⏱️  JSON parse:  {(time.time() - t0) * 1000:.0f} ms")

features = geo.get("features", [])
print(f"📍 Features:    {len(features)}")
if len(features) != 514:
    print(f"⚠️  Expected 514 — got {len(features)}")


# ════════════════════════════════════════════════════════════════════
# Step 3 — Coordinate complexity
# ════════════════════════════════════════════════════════════════════
print()
print("=" * 60)
print("STEP 3 — Coordinate complexity")
print("=" * 60)

total = 0
per_feature = []
for f in features:
    n = count_coords(f.get("geometry", {}).get("coordinates", []))
    total += n
    per_feature.append((n, f.get("properties", {}).get("kemendagri_kab_name", "?")))

per_feature.sort(reverse=True)

print(f"Total coordinate points (all 514 features): {total:,}")
print(f"Average per feature: {total // max(len(features), 1):,}")
print(f"\nTop 5 most complex regencies:")
for n, name in per_feature[:5]:
    print(f"   {n:>7,} points · {name}")

if total > 500_000:
    print(f"\n🚨 TOO MANY COORDINATES — Plotly will struggle to render.")
    print(f"   Web-resolution should be under 200,000 total.")
    needs_simplify = True
elif total > 200_000:
    print(f"\n⚠️  High coordinate count. May render slowly.")
    needs_simplify = True
else:
    print(f"\n✅ Coordinate count looks fine.")
    needs_simplify = False


# ════════════════════════════════════════════════════════════════════
# Step 4 — Required properties
# ════════════════════════════════════════════════════════════════════
print()
print("=" * 60)
print("STEP 4 — Required properties on each feature")
print("=" * 60)

REQUIRED_PROPS = ["kemendagri_kab_code", "kemendagri_kab_name"]
prop_counts = {p: 0 for p in REQUIRED_PROPS}
for f in features:
    props = f.get("properties", {}) or {}
    for p in REQUIRED_PROPS:
        if p in props and props[p] is not None:
            prop_counts[p] += 1

for p in REQUIRED_PROPS:
    status = "✅" if prop_counts[p] == len(features) else "❌"
    print(f"   {status} {p}: {prop_counts[p]} / {len(features)} features")


# ════════════════════════════════════════════════════════════════════
# Step 5 — Key match against regency_table.parquet
# ════════════════════════════════════════════════════════════════════
print()
print("=" * 60)
print("STEP 5 — Key match: parquet ↔ geojson")
print("=" * 60)

if not PARQUET_PATH.exists():
    print(f"⚠️  Skipping — {PARQUET_PATH} not found")
else:
    try:
        import pandas as pd
        df = pd.read_parquet(PARQUET_PATH)
        if "kemendagri_kab_code" not in df.columns:
            print(f"❌ regency_table.parquet missing kemendagri_kab_code column")
        else:
            parquet_codes = set(df["kemendagri_kab_code"].astype(str))
            geo_codes = {
                str(f.get("properties", {}).get("kemendagri_kab_code"))
                for f in features
            }
            both    = parquet_codes & geo_codes
            only_pq = parquet_codes - geo_codes
            only_gj = geo_codes - parquet_codes
            print(f"   Parquet codes:        {len(parquet_codes)}")
            print(f"   GeoJSON codes:        {len(geo_codes)}")
            print(f"   Matching (will draw): {len(both)}")
            if only_pq:
                print(f"   ⚠️  In parquet but NOT geojson: {len(only_pq)}")
                print(f"       Sample: {sorted(only_pq)[:5]}")
            if only_gj:
                print(f"   ⚠️  In geojson but NOT parquet: {len(only_gj)}")
                print(f"       Sample: {sorted(only_gj)[:5]}")
    except ImportError:
        print(f"⚠️  Skipping — pandas/pyarrow not installed in this env")


# ════════════════════════════════════════════════════════════════════
# Step 6 — Simplify if needed
# ════════════════════════════════════════════════════════════════════
print()
print("=" * 60)
print("STEP 6 — Simplification")
print("=" * 60)

if not needs_simplify:
    print("✅ Original geojson is already web-friendly. No action needed.")
    sys.exit(0)

try:
    import geopandas as gpd
except ImportError:
    print("❌ geopandas not installed — cannot simplify automatically.")
    print()
    print("   Option A — install geopandas:")
    print("       pip install geopandas")
    print()
    print("   Option B — simplify with mapshaper.org (GUI, web-based):")
    print("       1. Open https://mapshaper.org/")
    print("       2. Drag regencies.geojson onto the page")
    print("       3. Simplify menu → set ~5% retention, weighted")
    print("       4. Export as GeoJSON → save as regencies_simplified.geojson")
    print()
    print("   Option C — re-run nb11 with higher tolerance.")
    sys.exit(1)

print("📦 Loading with geopandas...")
gdf = gpd.read_file(GEO_PATH)
print(f"   Loaded {len(gdf)} features, CRS = {gdf.crs}")

# Ensure EPSG:4326
if gdf.crs is None or gdf.crs.to_epsg() != 4326:
    print(f"   Re-projecting to EPSG:4326...")
    gdf = gdf.to_crs(epsg=4326)

# Check validity
print(f"   Checking geometry validity...")
invalid = gdf[~gdf.is_valid]
if len(invalid) > 0:
    print(f"   ⚠️  {len(invalid)} invalid geometries — auto-fixing with buffer(0)")
    gdf["geometry"] = gdf.geometry.buffer(0)

# Simplify — target file size 2-5 MB
# Tolerance is in degrees for EPSG:4326. 0.01° ≈ 1.1 km — good for web maps.
for tolerance in [0.005, 0.01, 0.02, 0.03]:
    print(f"\n   Trying tolerance = {tolerance}°...")
    simplified = gdf.copy()
    simplified["geometry"] = gdf.geometry.simplify(tolerance, preserve_topology=True)

    # Write to a temp path to measure size
    simplified.to_file(OUT_PATH, driver="GeoJSON")
    out_size = OUT_PATH.stat().st_size / (1024 * 1024)

    # Re-count coords
    with open(OUT_PATH, "r", encoding="utf-8") as f:
        check = json.load(f)
    new_total = sum(
        count_coords(feat.get("geometry", {}).get("coordinates", []))
        for feat in check.get("features", [])
    )
    print(f"      → {out_size:.2f} MB, {new_total:,} coords")

    if 2 <= out_size <= 5 and new_total < 200_000:
        print(f"   ✅ Found good tolerance: {tolerance}°")
        break
else:
    print(f"   ⚠️  Couldn't reach 2-5 MB target. Using last result.")

print(f"\n✅ Wrote simplified geojson to:")
print(f"   {OUT_PATH}")
print()
print("NEXT STEP — point your dashboard at the simplified file.")
print("Edit lib/data_flood.py, in load_regencies_geojson():")
print()
print('    return _read_json(str(_GEO_DIR / "regencies_simplified.geojson"))')
print()
print("Restart Streamlit, hard-refresh browser (Ctrl+F5). Choropleth should render.")
