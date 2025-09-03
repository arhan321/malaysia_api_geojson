import os
import math
from typing import Optional, List, Dict
from dotenv import load_dotenv

import pandas as pd
import geopandas as gpd
from geopy.distance import geodesic

from fastapi import FastAPI, Query, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field

# =========================
# Konfigurasi & Data Path
# =========================
load_dotenv()
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
GEOJSON_PATH = os.getenv("GEOJSON_PATH", "mapsjatebg.geojson")
API_KEY = os.getenv("API_KEY", "secret123")
API_KEY_NAME = "X-API-Key"

TAGS_METADATA = [
    {"name": "system", "description": "Liveness/Readiness & metadata aplikasi."},
    {"name": "wisata", "description": "Endpoint rekomendasi objek wisata terdekat."},
]

# =========================
# API Key Dependency
# =========================
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == API_KEY:
        return api_key
    # (opsional) ganti ke status_code=401 kalau mau "Unauthorized"
    raise HTTPException(status_code=403, detail="API key tidak valid")

# =========================
# App (proteksi GLOBAL)
# =========================
app = FastAPI(
    title="Pariwisata API",
    description="API rekomendasi objek wisata terdekat berbasis GeoJSON",
    version=APP_VERSION,
    openapi_tags=TAGS_METADATA,
    dependencies=[Depends(get_api_key)],  # <<— semua endpoint wajib API key
)

# =========================
# Utils
# =========================
def _extract_xy(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf2 = gdf.copy()
    if "x" in gdf2.columns and "y" in gdf2.columns:
        return gdf2
    if "geometry" in gdf2.columns:
        if gdf2.crs is None:
            gdf2.set_crs(epsg=4326, inplace=True)
        else:
            gdf2 = gdf2.to_crs(epsg=4326)
        pts = gdf2["geometry"].apply(
            lambda geom: geom if geom.geom_type == "Point" else geom.representative_point()
        )
        gdf2["x"] = pts.apply(lambda p: float(p.x))
        gdf2["y"] = pts.apply(lambda p: float(p.y))
        return gdf2
    raise ValueError("Data tidak memiliki kolom x/y maupun geometry")

def _safe_str(s: pd.Series) -> pd.Series:
    return s.astype(str).fillna("")

def _choose_name_column(gdf: gpd.GeoDataFrame) -> Optional[str]:
    for cand in ["nama_objek", "Nama", "name", "NAMOBJ", "namobj"]:
        if cand in gdf.columns:
            return cand
    return None

def _geodesic_km(a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
    return geodesic((a_lat, a_lon), (b_lat, b_lon)).kilometers

# =========================
# Cache data
# =========================
try:
    gdf_raw = gpd.read_file(GEOJSON_PATH)
    gdf_raw.columns = gdf_raw.columns.str.strip()
    gdf_raw = _extract_xy(gdf_raw)
    NAME_COL = _choose_name_column(gdf_raw)
    DATA_LOADED = not gdf_raw.empty
except Exception:
    gdf_raw = gpd.GeoDataFrame()
    NAME_COL = None
    DATA_LOADED = False

# =========================
# Response Model
# =========================
class Recommendation(BaseModel):
    name: str = Field(..., description="Nama objek wisata")
    latitude: float
    longitude: float
    distance_km: float

class RecommendationResponse(BaseModel):
    user_location: Dict[str, float]
    topk: List[Recommendation]

class MetadataResponse(BaseModel):
    status: str
    version: str
    data_loaded: bool
    api_key_required: bool

# =========================
# Endpoints (semua protected)
# =========================
@app.get("/health", response_model=MetadataResponse, tags=["system"])
def health_check():
    return MetadataResponse(
        status="ok",
        version=APP_VERSION,
        data_loaded=DATA_LOADED,
        api_key_required=True
    )

@app.get("/recommend", response_model=RecommendationResponse, tags=["wisata"])
def recommend(
    lat: float = Query(..., description="Latitude lokasi user"),
    lon: float = Query(..., description="Longitude lokasi user"),
    k: int = Query(3, description="Jumlah rekomendasi terdekat"),
    radius_km: Optional[float] = Query(None, description="Radius filter dalam km"),
    name: Optional[str] = Query(None, description="Filter nama objek wisata"),
):
    gdf = gdf_raw.copy()

    if name and NAME_COL:
        gdf = gdf[_safe_str(gdf[NAME_COL]).str.lower() == name.lower()]
    if gdf.empty:
        raise HTTPException(status_code=404, detail="Tidak ada data setelah filter")

    gdf["distance_km"] = gdf.apply(
        lambda r: _geodesic_km(lat, lon, float(r["y"]), float(r["x"])), axis=1
    )

    gdf_sorted = gdf.sort_values("distance_km")
    if radius_km:
        gdf_sorted = gdf_sorted[gdf_sorted["distance_km"] <= radius_km]

    topk = gdf_sorted.head(k)
    if topk.empty:
        raise HTTPException(status_code=404, detail="Tidak ada objek dalam radius/top-k")

    results = [
        Recommendation(
            name=str(r[NAME_COL]) if NAME_COL else "Objek",
            latitude=float(r["y"]),
            longitude=float(r["x"]),
            distance_km=float(r["distance_km"]),
        )
        for _, r in topk.iterrows()
    ]

    return RecommendationResponse(
        user_location={"latitude": lat, "longitude": lon},
        topk=results,
    )

# =========================
# Custom OpenAPI (Swagger Auth global)
# =========================
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema.setdefault("components", {}).setdefault("securitySchemes", {})
    schema["components"]["securitySchemes"]["APIKeyHeader"] = {
        "type": "apiKey",
        "in": "header",
        "name": API_KEY_NAME,
    }
    # Security global → berlaku untuk semua operasi
    schema["security"] = [{"APIKeyHeader": []}]
    app.openapi_schema = schema
    return app.openapi_schema

app.openapi = custom_openapi
