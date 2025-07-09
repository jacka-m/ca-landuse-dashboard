import geopandas as gpd
import rasterio
from rasterio.mask import mask
import pandas as pd
from pathlib import Path

# 1. Load CA boundary from local GeoJSON
ca = gpd.read_file('data/ca_boundary.geojson')

# 2. Define recoding map
class_map = {
    41: "Forest", 42: "Forest", 43: "Forest", 52: "Shrubland",
    81: "Agriculture", 82: "Agriculture",
    21: "Urban", 22: "Urban", 23: "Urban", 24: "Urban",
    90: "Wetlands", 95: "Wetlands", 11: "Water"
}

# 3. Loop over all GeoTIFFs and build summary
records = []
for tif in sorted(Path('data').glob('*.tif')):
    # Extract year (assumes name like ..._2001_...tif)
    year = int(tif.stem.split('_')[1])
    with rasterio.open(tif) as src:
        # Reproject boundary if needed
        if ca.crs != src.crs:
            ca = ca.to_crs(src.crs)
        # Clip
        out_img, _ = mask(src, ca.geometry, crop=True)
        arr = out_img[0].flatten()
    # Filter nodata (assume code 0) and count
    arr = arr[arr != 0]
    counts = pd.Series(arr).value_counts()
    # Record areas
    for code, cnt in counts.items():
        category = class_map.get(int(code), "Other")
        area_ha = cnt * (900 / 10000)  # 900 m² per pixel → ha
        records.append({"year": year, "category": category, "area_ha": area_ha})

# 4. Compile and save
df = pd.DataFrame(records)
df.to_csv('data/landcover_summary.csv', index=False)
print("→ Saved multi‐year summary to data/landcover_summary.csv")
