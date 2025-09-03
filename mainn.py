import os
import math
from typing import Optional, List, Dict, Any

import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium

# ===== Optional geolocation (pakai salah satu yang tersedia) =====
def _try_import_js_loc():
    # Prioritas 1: streamlit-js-eval
    try:
        from streamlit_js_eval import get_geolocation  # pip install streamlit-js-eval
        def get_browser_location():
            try:
                loc = get_geolocation()
                if loc and isinstance(loc, dict) and loc.get("coords"):
                    return float(loc["coords"]["latitude"]), float(loc["coords"]["longitude"])
            except Exception:
                pass
            return None
        return get_browser_location
    except Exception:
        pass

    # Prioritas 2: streamlit_javascript
    try:
        from streamlit_javascript import st_javascript  # pip install streamlit-javascript
        def get_browser_location():
            try:
                loc = st_javascript("""
                new Promise((resolve) => {
                    navigator.geolocation.getCurrentPosition(
                        (pos) => resolve({latitude: pos.coords.latitude, longitude: pos.coords.longitude}),
                        (err) => resolve(null),
                        { enableHighAccuracy: true, timeout: 8000, maximumAge: 0 }
                    );
                });
                """)
                if isinstance(loc, dict) and "latitude" in loc and "longitude" in loc:
                    return float(loc["latitude"]), float(loc["longitude"])
            except Exception:
                pass
            return None
        return get_browser_location
    except Exception:
        pass

    # Fallback: tidak ada modul geolocation
    def get_browser_location():
        return None
    return get_browser_location

get_browser_location = _try_import_js_loc()

# =========================
# Konfigurasi & Data Path
# =========================
st.set_page_config(page_title="Peta & Rekomendasi Pariwisata", layout="wide")
GEOJSON_PATH = os.getenv("GEOJSON_PATH", "mapsjatebg.geojson")

# =========================
# Utils (disalin dari versi API, disesuaikan)
# =========================
def _extract_xy(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Pastikan ada kolom x (lon) dan y (lat). Pakai x/y jika ada, kalau tidak ambil dari geometry."""
    gdf2 = gdf.copy()
    # Normalisasi nama kolom untuk cek
    lower_cols = {c.lower(): c for c in gdf2.columns}
    has_x = "x" in lower_cols
    has_y = "y" in lower_cols

    if has_x and has_y:
        # pastikan nama kolom x/y tepat (kalau aslinya kapital)
        if lower_cols["x"] != "x":
            gdf2.rename(columns={lower_cols["x"]: "x"}, inplace=True)
        if lower_cols["y"] != "y":
            gdf2.rename(columns={lower_cols["y"]: "y"}, inplace=True)
        return gdf2

    # Ambil dari geometry
    if "geometry" in gdf2.columns:
        try:
            if gdf2.crs is None:
                gdf2.set_crs(epsg=4326, inplace=True)
            else:
                gdf2 = gdf2.to_crs(epsg=4326)
        except Exception:
            pass

        def to_point(geom):
            if geom is None or geom.is_empty:
                return None
            if geom.geom_type == "Point":
                return geom
            try:
                return geom.representative_point()
            except Exception:
                try:
                    return geom.centroid
                except Exception:
                    return None

        pts = gdf2["geometry"].apply(to_point)
        gdf2["x"] = pts.apply(lambda p: float(p.x) if p else math.nan)
        gdf2["y"] = pts.apply(lambda p: float(p.y) if p else math.nan)
        return gdf2

    raise ValueError("Data tidak memiliki kolom x/y maupun geometry untuk diekstrak.")

def _safe_str(s: pd.Series) -> pd.Series:
    return s.astype(str).fillna("")

def _choose_name_column(gdf: gpd.GeoDataFrame) -> Optional[str]:
    for cand in ["nama_objek", "Nama", "name", "NAMOBJ", "namobj"]:
        if cand in gdf.columns:
            return cand
    return None

def _compute_point(geom, method: str):
    if geom is None or (hasattr(geom, "is_empty") and geom.is_empty):
        return None
    if geom.geom_type == "Point":
        return geom
    if method == "Centroid":
        return geom.centroid
    return geom.representative_point()

def _geodesic_km(a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
    return geodesic((a_lat, a_lon), (b_lat, b_lon)).kilometers

# =========================
# Cache loading
# =========================
@st.cache_data(show_spinner=False)
def load_geojson(path: str) -> gpd.GeoDataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"GeoJSON tidak ditemukan: {path}")
    gdf = gpd.read_file(path)
    gdf.columns = gdf.columns.str.strip()
    gdf2 = _extract_xy(gdf)
    return gdf2

# =========================
# Load data
# =========================
try:
    gdf_raw = load_geojson(GEOJSON_PATH)
except Exception as e:
    st.error(f"❌ Gagal memuat data: {e}")
    st.stop()

name_col = _choose_name_column(gdf_raw)
all_names = []
if name_col:
    all_names = sorted(_safe_str(gdf_raw[name_col]).dropna().unique().tolist())

# =========================
# Sidebar Controls
# =========================
st.sidebar.header("⚙️ Pengaturan")

# Filter nama objek
selected_name = st.sidebar.selectbox(
    "Pilih Nama Objek", 
    ["Semua"] + all_names if all_names else ["Semua"],
    index=0
)

# Metode titik geometri (untuk geometri non-point)
geom_method = st.sidebar.radio("Metode titik geometri", ["Representative Point", "Centroid"], index=0)

# K rekomendasi & Radius
k = st.sidebar.number_input("Jumlah rekomendasi (Top-K)", min_value=1, max_value=100, value=3, step=1)
use_radius = st.sidebar.checkbox("Filter dengan radius (km)", value=False)
radius_km = st.sidebar.number_input("Radius (km)", min_value=0.1, max_value=500.0, value=10.0, step=0.5) if use_radius else None

# Lokasi pengguna
st.sidebar.subheader("📍 Lokasi Anda")
use_browser_loc = st.sidebar.checkbox("Gunakan lokasi dari browser (jika tersedia)", value=True)
DEFAULT_LAT, DEFAULT_LON = -7.4, 110.3  # contoh Jogja
lat, lon = DEFAULT_LAT, DEFAULT_LON

if use_browser_loc:
    loc = get_browser_location()
    if loc:
        lat, lon = loc
        st.sidebar.success(f"Dapat lokasi browser: {lat:.6f}, {lon:.6f}")
    else:
        st.sidebar.info("Tidak bisa membaca lokasi browser. Isi manual di bawah.")

lat = st.sidebar.number_input("Latitude", value=float(lat), format="%.6f")
lon = st.sidebar.number_input("Longitude", value=float(lon), format="%.6f")

# =========================
# Filtering data
# =========================
gdf = gdf_raw.copy()
if selected_name and selected_name != "Semua" and name_col:
    gdf = gdf[_safe_str(gdf[name_col]).str.lower() == selected_name.lower()]

if gdf.empty:
    st.warning("Data kosong setelah filter. Tampilkan semua data.")
    gdf = gdf_raw.copy()

# Siapkan titik representatif bila perlu, dan pastikan x/y mengikuti pilihan metode
if "geometry" in gdf.columns:
    pts = gdf["geometry"].apply(lambda g: _compute_point(g, geom_method))
    gdf["x"] = pts.apply(lambda p: float(p.x) if p is not None else math.nan)
    gdf["y"] = pts.apply(lambda p: float(p.y) if p is not None else math.nan)

# Drop baris tanpa koordinat
gdf = gdf.dropna(subset=["x", "y"])

# =========================
# Hitung jarak & tentukan hasil
# =========================
gdf = gdf.copy()
gdf["distance_km"] = gdf.apply(lambda r: _geodesic_km(float(lat), float(lon), float(r["y"]), float(r["x"])), axis=1)

gdf_sorted = gdf.sort_values("distance_km")
if use_radius and radius_km is not None:
    gdf_sorted = gdf_sorted[gdf_sorted["distance_km"] <= float(radius_km)]

topk = gdf_sorted.head(int(k))
nearest = topk.iloc[0] if not topk.empty else gdf.sort_values("distance_km").iloc[0]

# =========================
# Header & Ringkasan
# =========================
st.title("🗺️ Peta & Rekomendasi Pariwisata Terdekat")
colA, colB = st.columns(2)
with colA:
    st.write(f"📍 **Lokasi Anda:** {lat:.6f}, {lon:.6f}")
    if use_radius and radius_km is not None:
        st.write(f"🎯 **Radius filter:** {radius_km:.2f} km")
    st.write(f"🔢 **Top-K:** {k}")

with colB:
    if not topk.empty:
        nm = nearest.get(name_col, None)
        nm = nm if pd.notna(nm) else "—"
        st.success(f"⭐ **Terdekat:** {nm} — {nearest['distance_km']:.2f} km")
    else:
        st.warning("Tidak ada objek dalam radius. Menampilkan rute ke terdekat secara global.")

# =========================
# Tabel hasil (tanpa geometry)
# =========================
st.subheader("📋 Hasil (Terdekat)")
hide_cols = {"geometry"}
show_cols = [c for c in gdf.columns if c not in hide_cols]
if not topk.empty:
    st.dataframe(
        topk[show_cols]
        .rename(columns={"x": "longitude", "y": "latitude", "distance_km": "jarak_km"})
        .reset_index(drop=True)
    )
else:
    st.info("Tidak ada hasil untuk ditampilkan.")

# =========================
# Peta Folium
# =========================
st.subheader("🧭 Peta Interaktif")
m = folium.Map(location=[lat, lon], zoom_start=12, control_scale=True, tiles="CartoDB positron")

# Marker lokasi pengguna
folium.Marker(
    [lat, lon],
    popup="Lokasi Anda",
    icon=folium.Icon(color="red", icon="user")
).add_to(m)

# Marker hasil (pakai topk kalau ada, else ambil 1 terdekat global agar tetap informatif)
plot_df = topk if not topk.empty else gdf.sort_values("distance_km").head(1)
nmcol = name_col if name_col else None

for _, r in plot_df.iterrows():
    gm_lat, gm_lon = float(r["y"]), float(r["x"])
    label = str(r[nmcol]) if nmcol and pd.notna(r.get(nmcol, None)) else "Objek"
    jarak = float(r["distance_km"])
    # Link arah
    gmaps_url = f"https://www.google.com/maps/dir/{lat},{lon}/{gm_lat},{gm_lon}"
    popup_html = f"<b>{label}</b><br>{jarak:.2f} km<br><a href='{gmaps_url}' target='_blank'>Arah (Google Maps)</a>"
    folium.Marker(
        [gm_lat, gm_lon],
        popup=folium.Popup(popup_html, max_width=280),
        icon=folium.Icon(color="green", icon="star")
    ).add_to(m)

    # Polyline rute lurus
    folium.PolyLine(
        locations=[(lat, lon), (gm_lat, gm_lon)],
        color="blue", weight=3, opacity=0.8, dash_array="6,6"
    ).add_to(m)

# (Opsional) tampilkan seluruh layer GeoJSON sebagai overlay dengan tooltip
show_geo_layer = st.checkbox("Tampilkan layer GeoJSON (tooltip semua kolom non-geometry)", value=False)
if show_geo_layer:
    tooltip_fields = [c for c in gdf_raw.columns if c != "geometry"]
    folium.GeoJson(
        gdf_raw, name="Layer GeoJSON",
        tooltip=folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_fields, localize=True)
    ).add_to(m)
    folium.LayerControl().add_to(m)

st_folium(m, width=950, height=560)
