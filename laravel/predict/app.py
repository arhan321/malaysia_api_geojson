from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader, APIKey
from pydantic import BaseModel, Field
from typing import List, Literal, Optional

import pandas as pd
import geopandas as gpd
from geopy.distance import geodesic
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor

# =========================
# Konfigurasi & Path Data
# =========================
EXCEL_PATH = "estimasi_wisata.xlsx"      # <<-- disesuaikan
GEOJSON_PATH = "wisata_diy.geojson"      # <<-- disesuaikan

API_KEY = "berapaya"  # ganti sesuai kebutuhan
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

app = FastAPI(title="Berapa Ya - Wisata DIY",
              description="Prototype prediksi biaya & pencarian tempat wisata di DIY",
              version="1.2.0")

# CORS (opsional)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# Security Dependency
# =========================
async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(status_code=403, detail="Could not validate API KEY")

# =========================
# Utilitas
# =========================
def compute_distance_km(latlon_a, latlon_b) -> float:
    return geodesic(latlon_a, latlon_b).km


def filter_only_wisata(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Ambil hanya fitur tempat wisata.
    Prefer 'tourism' ∈ {attraction, museum, viewpoint, park, beach}, 
    jika tak ada, fallback pakai kata kunci di nama/kategori.
    """
    g = gdf.copy()
    allowed = {"attraction", "museum", "viewpoint", "park", "beach"}
    mask = pd.Series(False, index=g.index)

    if "tourism" in g.columns:
        mask |= g["tourism"].astype(str).str.lower().isin(allowed)

    for c in ["NAMOBJ", "KATEGORI"]:
        if c in g.columns:
            mask |= g[c].astype(str).str.contains(
                r"(candi|pantai|museum|taman|landmark|view|sunset|geowisata|kuliner|panorama)",
                case=False, regex=True, na=False
            )

    return g[mask] if mask.any() else g


# =========================
# Model & Data Global (di-load saat startup)
# =========================
DF: Optional[pd.DataFrame] = None
GDF_POI: Optional[gpd.GeoDataFrame] = None
MODEL: Optional[RandomForestRegressor] = None
LABEL_ENCODERS: Optional[dict] = None


# =========================
# Schemas (Wisata)
# =========================
class PredictRequest(BaseModel):
    destinasi: str = Field(..., description="Nama destinasi persis seperti di Excel")
    budget: int = Field(250_000, description="Budget pengguna (Rupiah)")
    lat: float = Field(-7.7956, description="Latitude pengguna (default Yogyakarta)")
    lon: float = Field(110.3695, description="Longitude pengguna (default Yogyakarta)")
    radius_km: float = Field(10, ge=1, description="Radius pencarian tempat wisata dalam km")
    geom_method: Literal["Centroid", "Representative Point"] = Field(
        "Representative Point", description="Metode titik perwakilan geometri"
    )


class PlaceOut(BaseModel):
    name: str
    lat: float
    lon: float
    distance_km: float
    google_maps_directions: str


class PredictResponse(BaseModel):
    destinasi: str
    predicted_cost: float
    budget: int
    budget_ok: bool
    radius_km: float
    places_in_radius: List[PlaceOut]
    count_in_radius: int
    nearest_place: PlaceOut
    note: Optional[str] = None


# =========================
# Startup: load Excel & GeoJSON
# =========================
@app.on_event("startup")
def on_startup():
    global DF, GDF_POI, MODEL, LABEL_ENCODERS

    # ---- Load Excel (estimasi_wisata.xlsx)
    df = pd.read_excel(EXCEL_PATH)
    df.columns = df.columns.str.strip()

    required_cols = [
        "Kategori", "Destinasi", "Aktivitas Utama",
        "Estimasi Biaya Min (Rp)", "Estimasi Biaya Max (Rp)"
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise RuntimeError(f"Kolom tidak lengkap di Excel: {missing}. Kolom ada: {list(df.columns)}")

    # Encode label & train model (prototype)
    df_enc = df.copy()
    label_encoders = {}
    for col in ["Kategori", "Destinasi", "Aktivitas Utama"]:
        le = LabelEncoder()
        df_enc[col] = le.fit_transform(df_enc[col].astype(str))
        label_encoders[col] = le

    X = df_enc[[
        "Kategori", "Destinasi", "Aktivitas Utama",
        "Estimasi Biaya Min (Rp)", "Estimasi Biaya Max (Rp)"
    ]]
    y = (df_enc["Estimasi Biaya Min (Rp)"] + df_enc["Estimasi Biaya Max (Rp)"]) / 2.0

    model = RandomForestRegressor(n_estimators=250, random_state=42, n_jobs=-1)
    model.fit(X, y)

    # ---- Load GeoJSON (wisata_diy.geojson) & siapkan CRS
    gdf = gpd.read_file(GEOJSON_PATH)
    try:
        if gdf.crs is None:
            gdf.set_crs(epsg=4326, inplace=True)
        else:
            gdf = gdf.to_crs(epsg=4326)
    except Exception:
        pass

    # Pastikan ada kolom nama destinasi
    if "NAMOBJ" not in gdf.columns:
        # fallback rename kalau file memakai 'name'
        if "name" in gdf.columns:
            gdf = gdf.rename(columns={"name": "NAMOBJ"})
        else:
            raise RuntimeError(f"GeoJSON wajib punya kolom 'NAMOBJ'. Kolom tersedia: {list(gdf.columns)}")

    gdf_poi = filter_only_wisata(gdf)

    # Precompute titik centroid & representative point untuk efisiensi
    gdf_poi = gdf_poi.copy()
    gdf_poi["centroid_point"] = gdf_poi.geometry.centroid
    gdf_poi["repr_point"] = gdf_poi.geometry.representative_point()
    gdf_poi["centroid_lat"] = gdf_poi["centroid_point"].y
    gdf_poi["centroid_lon"] = gdf_poi["centroid_point"].x
    gdf_poi["repr_lat"] = gdf_poi["repr_point"].y
    gdf_poi["repr_lon"] = gdf_poi["repr_point"].x

    # Simpan ke global
    DF = df
    GDF_POI = gdf_poi
    MODEL = model
    LABEL_ENCODERS = label_encoders


# =========================
# Endpoints
# =========================
@app.get("/health")
def health(api_key: APIKey = Depends(get_api_key)):
    return {"status": "ok"}


@app.get("/metadata")
def metadata(api_key: APIKey = Depends(get_api_key)):
    assert DF is not None
    return {
        "destinasi_list": sorted(list(map(str, DF["Destinasi"].unique()))),
        "kategori_list": sorted(list(map(str, DF["Kategori"].unique()))),
        "aktivitas_list": sorted(list(map(str, DF["Aktivitas Utama"].unique()))),
        "example_request": {
            "destinasi": str(DF["Destinasi"].iloc[0]),
            "budget": 250000,
            "lat": -7.7956,
            "lon": 110.3695,
            "radius_km": 10,
            "geom_method": "Representative Point"
        }
    }


@app.post("/predict-nearby", response_model=PredictResponse)
def predict_nearby(req: PredictRequest, api_key: APIKey = Depends(get_api_key)):
    if DF is None or GDF_POI is None or MODEL is None or LABEL_ENCODERS is None:
        raise HTTPException(status_code=503, detail="Model/data belum siap")

    # Validasi destinasi ada di data
    df_match = DF[DF["Destinasi"].astype(str) == req.destinasi]
    if df_match.empty:
        raise HTTPException(status_code=400, detail=f"Destinasi '{req.destinasi}' tidak ditemukan di Excel")

    row_sel = df_match.iloc[0]

    # Siapkan fitur prediksi
    X_pred = pd.DataFrame([{
        "Kategori": LABEL_ENCODERS["Kategori"].transform([row_sel["Kategori"]])[0],
        "Destinasi": LABEL_ENCODERS["Destinasi"].transform([row_sel["Destinasi"]])[0],
        "Aktivitas Utama": LABEL_ENCODERS["Aktivitas Utama"].transform([row_sel["Aktivitas Utama"]])[0],
        "Estimasi Biaya Min (Rp)": float(row_sel["Estimasi Biaya Min (Rp)"]),
        "Estimasi Biaya Max (Rp)": float(row_sel["Estimasi Biaya Max (Rp)"])
    }])

    predicted_cost = float(MODEL.predict(X_pred)[0])
    budget_ok = bool(req.budget >= predicted_cost)

    # Pilih titik geometri
    if req.geom_method == "Centroid":
        lat_col, lon_col = "centroid_lat", "centroid_lon"
    else:
        lat_col, lon_col = "repr_lat", "repr_lon"

    # Hitung jarak
    gdf_tmp = GDF_POI[["NAMOBJ", lat_col, lon_col]].copy()
    gdf_tmp.rename(columns={lat_col: "lat", lon_col: "lon"}, inplace=True)

    # Compute distances
    gdf_tmp["distance_km"] = gdf_tmp.apply(
        lambda r: compute_distance_km((req.lat, req.lon), (r["lat"], r["lon"])), axis=1
    )

    # Filter radius
    nearby = gdf_tmp[gdf_tmp["distance_km"] <= req.radius_km].sort_values("distance_km")
    note = None
    if nearby.empty:
        note = f"Tidak ada tempat wisata dalam radius {req.radius_km} km. Mengembalikan yang terdekat secara global."
        nearby = gdf_tmp.sort_values("distance_km").head(30)

    # Tempat terdekat (global atau dalam radius)
    nearest_row = nearby.iloc[0]

    def map_place_row(r: pd.Series) -> PlaceOut:
        url = f"https://www.google.com/maps/dir/{req.lat},{req.lon}/{float(r['lat'])},{float(r['lon'])}"
        return PlaceOut(
            name=str(r["NAMOBJ"]),
            lat=float(r["lat"]),
            lon=float(r["lon"]),
            distance_km=float(round(r["distance_km"], 4)),
            google_maps_directions=url,
        )

    places_out = [map_place_row(r) for _, r in nearby.iterrows()]
    nearest_out = map_place_row(nearest_row)

    return PredictResponse(
        destinasi=req.destinasi,
        predicted_cost=round(predicted_cost, 2),
        budget=req.budget,
        budget_ok=budget_ok,
        radius_km=req.radius_km,
        places_in_radius=places_out,
        count_in_radius=len(places_out) if note is None else 0,
        nearest_place=nearest_out,
        note=note,
    )


# =========================
# Cara Menjalankan:
# =========================
# 1) Install dependensi:
#    pip install fastapi uvicorn pandas geopandas geopy scikit-learn shapely pyproj fiona openpyxl
# 2) Jalankan server:
#    uvicorn app:app --reload --port 8000
# 3) Setiap request HARUS sertakan header:
#    X-API-Key: berapaya
# 4) Buka dokumentasi interaktif di:
#    http://127.0.0.1:8000/docs
