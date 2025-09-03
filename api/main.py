# api/main.py
import os
import sys
import math
import platform
import hashlib
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Literal, Tuple

import pandas as pd
import geopandas as gpd
from shapely.geometry.base import BaseGeometry
from geopy.distance import geodesic

from fastapi import FastAPI, Query, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# =========================
# Konfigurasi & Data Path
# =========================
GEOJSON_PATH = os.getenv("GEOJSON_PATH", "mapsjatebg.geojson")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
GIT_SHA = os.getenv("GIT_SHA", None)

TAGS_METADATA = [
    {"name": "system", "description": "Liveness/Readiness & metadata aplikasi."},
    {"name": "wisata", "description": "Endpoint rekomendasi & daftar objek wisata."},
]

app = FastAPI(
    title="Pariwisata API",
    description="API rekomendasi objek wisata terdekat berbasis GeoJSON (geodesic).",
    version=APP_VERSION,
    contact={"name": "Pariwisata API", "url": "https://example.com"},
    license_info={"name": "MIT"},
    openapi_tags=TAGS_METADATA,
)

# Izinkan akses dari mana saja (ubah sesuai kebutuhan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# =========================
# Model Respons
# =========================
class TouristItem(BaseModel):
    index: int = Field(..., description="Index baris asli pada data")
    nama_objek: Optional[str] = None
    jenis_obje: Optional[str] = None
    alamat: Optional[str] = None
    latitude: float
    longitude: float
    distance_km: Optional[float] = None
    properties: Dict[str, Any] = Field(default_factory=dict, description="Kolom lain (tanpa geometry)")

class NearestResponse(BaseModel):
    user_lat: float
    user_lon: float
    method: Literal["representative", "centroid"]
    k: int
    radius_km: Optional[float] = None
    count: int
    items: List[TouristItem]

class ObjectsResponse(BaseModel):
    count: int
    items: List[TouristItem]

class WisataStatus(BaseModel):
    status: str
    count: int
    name_column: Optional[str] = None

class MetaResponse(BaseModel):
    status: str
    ready: bool
    boot_time: str
    app_version: str
    git_sha: Optional[str]
    python_version: str
    platform: str
    libs: Dict[str, str]
    data: Dict[str, Any]

# =========================
# Utils
# =========================
def _safe_str(s: pd.Series) -> pd.Series:
    return s.astype(str).fillna("")

def _choose_name_column(gdf: gpd.GeoDataFrame) -> Optional[str]:
    for cand in ["nama_objek", "Nama", "name", "NAMOBJ", "namobj"]:
        if cand in gdf.columns:
            return cand
    return None

def _compute_point(geom: Optional[BaseGeometry], method: str):
    if geom is None or (hasattr(geom, "is_empty") and geom.is_empty):
        return None
    if geom.geom_type == "Point":
        return geom
    if method == "centroid":
        return geom.centroid
    # default representative point
    try:
        return geom.representative_point()
    except Exception:
        try:
            return geom.centroid
        except Exception:
            return None

def _geodesic_km(a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
    return geodesic((a_lat, a_lon), (b_lat, b_lon)).kilometers

def _extract_xy_base(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Pastikan minimal ada salah satu: (x,y) atau geometry. Normalisasi nama x/y jika sudah ada."""
    gdf2 = gdf.copy()
    gdf2.columns = gdf2.columns.str.strip()
    lower = {c.lower(): c for c in gdf2.columns}
    if "x" in lower and "y" in lower:
        if lower["x"] != "x":
            gdf2.rename(columns={lower["x"]: "x"}, inplace=True)
        if lower["y"] != "y":
            gdf2.rename(columns={lower["y"]: "y"}, inplace=True)
        return gdf2

    if "geometry" not in gdf2.columns:
        raise ValueError("Data tidak memiliki kolom x/y maupun geometry.")

    try:
        if gdf2.crs is None:
            gdf2.set_crs(epsg=4326, inplace=True)
        else:
            gdf2 = gdf2.to_crs(epsg=4326)
    except Exception:
        pass
    return gdf2

def _compute_xy_from_geom(gdf: gpd.GeoDataFrame, method: Literal["representative", "centroid"]) -> gpd.GeoDataFrame:
    """Hitung kolom x/y dari geometry sesuai method. Jika tidak ada geometry, kembalikan apa adanya."""
    gdf2 = _extract_xy_base(gdf)
    if "geometry" not in gdf2.columns:
        return gdf2
    pts = gdf2["geometry"].apply(lambda g: _compute_point(g, method))
    gdf2["x"] = pts.apply(lambda p: float(p.x) if p is not None else math.nan)
    gdf2["y"] = pts.apply(lambda p: float(p.y) if p is not None else math.nan)
    return gdf2

def _row_to_item(idx: int, row: pd.Series, include_distance: bool, name_col: Optional[str]) -> TouristItem:
    nama = None
    if name_col and name_col in row.index and pd.notna(row[name_col]):
        nama = str(row[name_col])
    else:
        for cand in ["nama_objek", "Nama", "name", "NAMOBJ", "namobj"]:
            if cand in row.index and pd.notna(row.get(cand, None)):
                nama = str(row[cand])
                break

    jenis = row.get("jenis_obje", None)
    alamat = row.get("alamat", None)

    lat = float(row["y"])
    lon = float(row["x"])
    dist = float(row["distance_km"]) if include_distance and "distance_km" in row.index and pd.notna(row["distance_km"]) else None

    drop_cols = {"geometry", "x", "y", "distance_km"}
    props = {k: (None if pd.isna(v) else v) for k, v in row.items() if k not in drop_cols}

    return TouristItem(
        index=int(idx),
        nama_objek=nama,
        jenis_obje=(None if pd.isna(jenis) else jenis) if "jenis_obje" in row.index else None,
        alamat=(None if pd.isna(alamat) else alamat) if "alamat" in row.index else None,
        latitude=lat,
        longitude=lon,
        distance_km=dist,
        properties=props,
    )

def _file_stats(path: str) -> Dict[str, Any]:
    st = os.stat(path)
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return {
        "path": os.path.abspath(path),
        "size_bytes": st.st_size,
        "mtime": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
        "sha256": h.hexdigest(),
    }

def _bbox_from_gdf(gdf: gpd.GeoDataFrame) -> Tuple[float, float, float, float]:
    if "geometry" in gdf.columns and gdf.geometry.notna().any():
        try:
            if gdf.crs is None:
                gdf2 = gdf.set_crs(epsg=4326, allow_override=True)
            else:
                gdf2 = gdf.to_crs(epsg=4326)
            minx, miny, maxx, maxy = gdf2.total_bounds
            return float(minx), float(miny), float(maxx), float(maxy)
        except Exception:
            pass
    # fallback dari x/y
    if {"x", "y"}.issubset(gdf.columns):
        return float(gdf["x"].min()), float(gdf["y"].min()), float(gdf["x"].max()), float(gdf["y"].max())
    return (0.0, 0.0, 0.0, 0.0)

# =========================
# Global (precompute pada startup)
# =========================
BOOT_TIME = datetime.now(tz=timezone.utc)
READY = False
GDF_BASE: Optional[gpd.GeoDataFrame] = None
GDF_REPR: Optional[gpd.GeoDataFrame] = None
GDF_CENT: Optional[gpd.GeoDataFrame] = None
NAME_COL: Optional[str] = None
DATA_STATS: Dict[str, Any] = {}
DATA_BBOX: Tuple[float, float, float, float] = (0, 0, 0, 0)

@app.on_event("startup")
def _load_data():
    global READY, GDF_BASE, GDF_REPR, GDF_CENT, NAME_COL, DATA_STATS, DATA_BBOX

    if not os.path.exists(GEOJSON_PATH):
        READY = False
        raise RuntimeError(f"GeoJSON tidak ditemukan: {GEOJSON_PATH}")

    # Load & normalize
    gdf = gpd.read_file(GEOJSON_PATH)
    gdf.columns = gdf.columns.str.strip()
    GDF_BASE = _extract_xy_base(gdf)
    NAME_COL = _choose_name_column(GDF_BASE)

    # Precompute XY utk 2 metode (hemat waktu request)
    GDF_REPR = _compute_xy_from_geom(GDF_BASE, "representative")
    GDF_CENT = _compute_xy_from_geom(GDF_BASE, "centroid")

    # File stats & bbox
    DATA_STATS = _file_stats(GEOJSON_PATH)
    DATA_BBOX = _bbox_from_gdf(GDF_BASE)

    READY = True

def _gdf_by_method(method: Literal["representative", "centroid"]) -> gpd.GeoDataFrame:
    if method == "centroid":
        return GDF_CENT if GDF_CENT is not None else GDF_REPR
    return GDF_REPR if GDF_REPR is not None else GDF_CENT

# =========================
# System / Health / Meta
# =========================
@app.get("/", tags=["system"])
def root():
    return {"message": "Pariwisata API up. Lihat /docs untuk dokumentasi."}

@app.get("/healthz", tags=["system"])
def healthz():
    """Liveness probe: server hidup."""
    if not READY:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Not ready")
    return {"status": "ok"}

@app.get("/readyz", tags=["system"])
def readyz():
    """Readiness probe: data sudah dimuat & siap melayani."""
    if not READY or GDF_BASE is None or len(GDF_BASE) == 0:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Not ready")
    return {"status": "ok", "rows": int(len(GDF_BASE))}

@app.get("/meta", response_model=MetaResponse, tags=["system"])
def meta():
    libs = {
        "pandas": pd.__version__,
        "geopandas": gpd.__version__,
        "python": sys.version.split()[0],
    }
    try:
        import shapely; libs["shapely"] = shapely.__version__
    except Exception:
        libs["shapely"] = "unknown"
    try:
        import geopy; libs["geopy"] = geopy.__version__
    except Exception:
        libs["geopy"] = "unknown"

    data = {
        "geojson": DATA_STATS,
        "rows": int(len(GDF_BASE)) if GDF_BASE is not None else 0,
        "name_column": NAME_COL,
        "bbox_wgs84": list(DATA_BBOX),
        "has_geometry": bool(GDF_BASE is not None and "geometry" in GDF_BASE.columns),
        "columns": list(GDF_BASE.columns) if GDF_BASE is not None else [],
    }

    return MetaResponse(
        status="ok",
        ready=READY,
        boot_time=BOOT_TIME.isoformat(),
        app_version=APP_VERSION,
        git_sha=GIT_SHA,
        python_version=platform.python_version(),
        platform=platform.platform(),
        libs=libs,
        data=data,
    )

# =========================
# Endpoints (prefix: /wisata)
# =========================
@app.get("/wisata", response_model=WisataStatus, tags=["wisata"])
def wisata_status():
    assert GDF_BASE is not None
    return WisataStatus(status="ok", count=len(GDF_BASE), name_column=NAME_COL)

@app.get("/wisata/names", response_model=List[str], tags=["wisata"])
def list_unique_names():
    assert GDF_BASE is not None
    gdf = GDF_BASE
    if NAME_COL and NAME_COL in gdf.columns:
        vals = gdf[NAME_COL].dropna().astype(str).unique().tolist()
        return sorted(vals)
    for cand in ["nama_objek", "Nama", "name", "NAMOBJ", "namobj"]:
        if cand in gdf.columns:
            vals = gdf[cand].dropna().astype(str).unique().tolist()
            return sorted(vals)
    return []

@app.get("/wisata/objects", response_model=ObjectsResponse, tags=["wisata"])
def list_objects(
    name: Optional[str] = Query(None, description="Filter tepat untuk nama (jika diketahui kolomnya)."),
    limit: int = Query(100, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    method: Literal["representative", "centroid"] = Query("representative", description="Metode titik dari geometry."),
):
    assert GDF_BASE is not None
    gdf = _gdf_by_method(method)

    # Filter nama jika diminta
    if name and name.lower() != "semua":
        mask = False
        for cand in [NAME_COL] + ["nama_objek", "Nama", "name", "NAMOBJ", "namobj"]:
            if cand and cand in gdf.columns:
                mask = mask | (_safe_str(gdf[cand]).str.lower() == name.lower())
        gdf = gdf[mask]

    total = len(gdf)
    if total == 0:
        return ObjectsResponse(count=0, items=[])

    sliced = gdf.iloc[offset : offset + limit]
    items = [_row_to_item(int(idx), row, include_distance=False, name_col=NAME_COL) for idx, row in sliced.iterrows()]
    return ObjectsResponse(count=total, items=items)

@app.get("/wisata/nearest", response_model=NearestResponse, tags=["wisata"])
def nearest_objects(
    lat: float = Query(..., description="Latitude pengguna"),
    lon: float = Query(..., description="Longitude pengguna"),
    k: int = Query(3, ge=1, le=100),
    name: Optional[str] = Query(None, description="Filter tepat untuk nama (opsional)"),
    radius_km: Optional[float] = Query(None, gt=0, description="Jika diisi, batasi hasil dalam radius ini"),
    method: Literal["representative", "centroid"] = Query("representative", description="Metode titik dari geometry."),
):
    assert GDF_BASE is not None
    gdf = _gdf_by_method(method)

    if name and name.lower() != "semua":
        mask = False
        for cand in [NAME_COL] + ["nama_objek", "Nama", "name", "NAMOBJ", "namobj"]:
            if cand and cand in gdf.columns:
                mask = mask | (_safe_str(gdf[cand]).str.lower() == name.lower())
        gdf = gdf[mask]

    if gdf.empty:
        raise HTTPException(status_code=404, detail="Data kosong setelah filter nama.")

    gdf = gdf.dropna(subset=["x", "y"]).copy()
    gdf["distance_km"] = gdf.apply(lambda r: _geodesic_km(float(lat), float(lon), float(r["y"]), float(r["x"])), axis=1)

    if radius_km is not None:
        gdf = gdf[gdf["distance_km"] <= radius_km]

    if gdf.empty:
        raise HTTPException(status_code=404, detail="Tidak ada objek dalam radius/kriteria.")

    gdf_sorted = gdf.sort_values("distance_km").head(k)
    items = [_row_to_item(int(idx), row, include_distance=True, name_col=NAME_COL) for idx, row in gdf_sorted.iterrows()]
    return NearestResponse(
        user_lat=lat,
        user_lon=lon,
        method=method,
        k=k,
        radius_km=radius_km,
        count=len(items),
        items=items,
    )

@app.get("/wisata/geojson", tags=["wisata"])
def nearest_as_geojson(
    lat: float = Query(..., description="Latitude pengguna"),
    lon: float = Query(..., description="Longitude pengguna"),
    k: int = Query(3, ge=1, le=100),
    name: Optional[str] = Query(None, description="Filter tepat untuk nama (opsional)"),
    radius_km: Optional[float] = Query(None, gt=0, description="Jika diisi, batasi hasil dalam radius ini"),
    method: Literal["representative", "centroid"] = Query("representative", description="Metode titik dari geometry."),
):
    """Hasil yang sama dengan /wisata/nearest namun dikembalikan dalam format GeoJSON FeatureCollection."""
    resp = nearest_objects(lat=lat, lon=lon, k=k, name=name, radius_km=radius_km, method=method)  # reuse logic
    features = []
    for it in resp.items:
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [it.longitude, it.latitude]},
            "properties": {
                "index": it.index,
                "nama_objek": it.nama_objek,
                "jenis_obje": it.jenis_obje,
                "alamat": it.alamat,
                "distance_km": it.distance_km,
                **it.properties,
            }
        })
    return {"type": "FeatureCollection", "features": features, "metadata": {
        "user": {"lat": resp.user_lat, "lon": resp.user_lon},
        "method": resp.method, "k": resp.k, "radius_km": resp.radius_km
    }}
