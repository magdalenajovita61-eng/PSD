"""
Crawling Data Polutan (CO, NO2, HCHO, O3, SO2, CH4) dari Sentinel-5P
menggunakan Google Earth Engine, dibatasi area dari file GeoJSON.

Cara pakai:
1. pip install earthengine-api geopandas pandas
2. Ganti PROJECT_ID di bawah dengan Google Cloud Project ID kamu
   (daftar dulu di https://code.earthengine.google.com/register)
3. Jalankan: python crawling_polutan.py
4. Hasil tersimpan di hasil_crawling_polutan.csv
"""

import ee
import geopandas as gpd
import pandas as pd

# ====== PENGATURAN ======
PROJECT_ID = "proyek-sain-data"      # ganti dengan project id GEE kamu
GEOJSON_PATH = "Tugas Pertama PSD.geojson"       # file geojson area
START_DATE = "2025-08-30"
END_DATE = "2026-08-30"
OUTPUT_CSV = "hasil_crawling_polutan.csv"

# Daftar polutan yang mau di-crawl beserta koleksi & band di Earth Engine
POLLUTANTS = {
    "CO":   ("COPERNICUS/S5P/OFFL/L3_CO",   "CO_column_number_density"),
    "NO2":  ("COPERNICUS/S5P/OFFL/L3_NO2",  "tropospheric_NO2_column_number_density"),
    "HCHO": ("COPERNICUS/S5P/OFFL/L3_HCHO", "tropospheric_HCHO_column_number_density"),
    "O3":   ("COPERNICUS/S5P/OFFL/L3_O3",   "O3_column_number_density"),
    "SO2":  ("COPERNICUS/S5P/OFFL/L3_SO2",  "SO2_column_number_density"),
    "CH4":  ("COPERNICUS/S5P/OFFL/L3_CH4",  "CH4_column_volume_mixing_ratio_dry_air"),
}


def init_earth_engine():
    try:
        ee.Initialize(project=PROJECT_ID)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=PROJECT_ID)


def load_area(path):
    gdf = gpd.read_file(path)
    geom = gdf.unary_union.convex_hull  # gabung semua fitur jadi satu area
    return ee.Geometry(geom.__geo_interface__)


def crawl_pollutant(name, collection_id, band, roi):
    collection = (
        ee.ImageCollection(collection_id)
        .select(band)
        .filterDate(START_DATE, END_DATE)
        .filterBounds(roi)
    )

    def get_mean(img):
        mean = img.reduceRegion(ee.Reducer.mean(), roi, 1113.2, maxPixels=1e13)
        return ee.Feature(None, {"date": img.date().format("YYYY-MM-dd"), "value": mean.get(band)})

    result = collection.map(get_mean).filter(ee.Filter.notNull(["value"])).getInfo()

    rows = []
    for f in result["features"]:
        p = f["properties"]
        rows.append({"date": p["date"], "pollutant": name, "value": p["value"]})

    print(f"{name}: {len(rows)} data ditemukan")
    return rows


def main():
    init_earth_engine()
    roi = load_area(GEOJSON_PATH)

    all_rows = []
    for name, (collection_id, band) in POLLUTANTS.items():
        all_rows.extend(crawl_pollutant(name, collection_id, band, roi))

    df = pd.DataFrame(all_rows)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nSelesai. Data tersimpan di {OUTPUT_CSV} ({len(df)} baris)")


if __name__ == "__main__":
    main()
