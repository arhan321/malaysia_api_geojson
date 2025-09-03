import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor
from shapely.geometry import Point

# ====== OPTIONAL geolocation (tanpa error kalau tidak terpasang) ======
try:
    from streamlit_js_eval import get_geolocation  # pip install streamlit-js-eval
    HAS_JS_EVAL = True
except Exception:
    HAS_JS_EVAL = False

# =========================
# Konfigurasi Halaman
# =========================
st.set_page_config(page_title="Prediksi Estimasi Biaya Rumah Sakit", layout="wide")

# =========================
# Path Data
# =========================
EXCEL_PATH = "Estimasi Biaya.xlsx"
GEOJSON_PATH = "rumah_sakit.geojson"

# =========================
# Helper & Cache
# =========================
@st.cache_data(show_spinner=False)
def load_excel(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)
    df.columns = df.columns.str.strip()
    return df

@st.cache_data(show_spinner=False)
def load_geojson(path: str) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(path)
    # pastikan WGS84 (lat/lon)
    try:
        if gdf.crs is None:
            gdf.set_crs(epsg=4326, inplace=True)
        else:
            gdf = gdf.to_crs(epsg=4326)
    except Exception:
        # kalau crs bermasalah, tetap lanjut
        pass
    return gdf

@st.cache_resource(show_spinner=False)
def train_model(data: pd.DataFrame):
    """Train RandomForest untuk estimasi biaya. Target = mean(Min, Max)."""
    df_enc = data.copy()
    label_encoders = {}
    for col in ["Kategori", "Penyakit", "Tindakan Medis Utama"]:
        le = LabelEncoder()
        df_enc[col] = le.fit_transform(df_enc[col].astype(str))
        label_encoders[col] = le

    X = df_enc[["Kategori", "Penyakit", "Tindakan Medis Utama", "Estimasi Min (Rp)", "Estimasi Max (Rp)"]]
    y = (df_enc["Estimasi Min (Rp)"] + df_enc["Estimasi Max (Rp)"]) / 2.0

    model = RandomForestRegressor(n_estimators=250, random_state=42, n_jobs=-1)
    model.fit(X, y)
    return model, label_encoders

def compute_point(geom, method: str):
    """Ambil titik perwakilan untuk geometri (centroid / representative_point)."""
    if method == "Centroid":
        pt = geom.centroid
    else:
        pt = geom.representative_point()
    return pt

def compute_distance_km(latlon_a, latlon_b) -> float:
    """Haversine via geopy.geodesic (km)."""
    return geodesic(latlon_a, latlon_b).km

def filter_only_hospitals(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Filter fitur yang merupakan Rumah Sakit. Mengandalkan kolom NAMOBJ/REMARK jika ada."""
    gdf2 = gdf.copy()
    cols = [c for c in gdf2.columns]
    # standar: NAMOBJ berisi nama fasilitas
    mask = pd.Series([False] * len(gdf2))
    if "NAMOBJ" in cols:
        mask = mask | gdf2["NAMOBJ"].str.contains("Rumah Sakit", case=False, na=False)
    # fallback: REMARK atau METADATA kadang menyebutkan tipe
    if "REMARK" in cols:
        mask = mask | gdf2["REMARK"].str.contains("Rumah Sakit", case=False, na=False)
    if "TIPSHT" in cols:
        mask = mask | gdf2["TIPSHT"].astype(str).str.contains("Rumah Sakit", case=False, na=False)

    filtered = gdf2[mask]
    # kalau hasil kosong, pakai semua (lebih baik tampil daripada kosong)
    return filtered if not filtered.empty else gdf2

def add_direction_popup(lat_from, lon_from, lat_to, lon_to, label="Arah (Google Maps)"):
    url = f"https://www.google.com/maps/dir/{lat_from},{lon_from}/{lat_to},{lon_to}"
    return folium.Popup(f'<a href="{url}" target="_blank">{label}</a>', max_width=250)

# =========================
# Load Data
# =========================
try:
    df = load_excel(EXCEL_PATH)
    gdf = load_geojson(GEOJSON_PATH)
except FileNotFoundError as e:
    st.error(f"❌ {e}")
    st.stop()

# Validasi kolom Excel
required_cols = ["Kategori", "Penyakit", "Tindakan Medis Utama", "Estimasi Min (Rp)", "Estimasi Max (Rp)"]
missing = [c for c in required_cols if c not in df.columns]
if missing:
    st.error(f"❌ Kolom tidak lengkap di Excel: {missing}\nKolom tersedia: {list(df.columns)}")
    st.stop()

# Validasi kolom untuk nama RS
if "NAMOBJ" not in gdf.columns:
    st.error(f"❌ GeoJSON tidak punya kolom 'NAMOBJ'. Kolom tersedia: {list(gdf.columns)}")
    st.stop()

# Filter hanya Rumah Sakit
gdf_hosp = filter_only_hospitals(gdf)
if gdf_hosp.empty:
    st.warning("⚠️ Tidak ada fitur 'Rumah Sakit' terdeteksi. Menampilkan semua fitur dari GeoJSON.")
    gdf_hosp = gdf.copy()

# Train model (cache)
model, label_encoders = train_model(df)

# =========================
# Sidebar - Input
# =========================
st.sidebar.header("🎯 Parameter")
penyakit = st.sidebar.selectbox("Pilih Penyakit", df["Penyakit"].unique())

budget = st.sidebar.number_input(
    "Masukkan Budget (Rp)",
    min_value=1_000_000,
    step=500_000,
    value=5_000_000
)

radius_options = [5, 10, 15, 20, 30, 50]
radius_km = st.sidebar.selectbox("Radius pencarian Rumah Sakit (km)", radius_options, index=1)

geom_method = st.sidebar.radio("Metode titik geometri untuk jarak", ["Centroid", "Representative Point"], index=1)

use_auto_loc = st.sidebar.checkbox("Gunakan lokasi saya (browser)", value=True if HAS_JS_EVAL else False,
                                   help="Butuh izin lokasi browser & paket streamlit-js-eval.")

# Lokasi user
DEFAULT_LAT, DEFAULT_LON = -6.2, 106.8  # Jakarta
lat, lon = DEFAULT_LAT, DEFAULT_LON

if use_auto_loc and HAS_JS_EVAL:
    try:
        loc = get_geolocation()
        if loc and isinstance(loc, dict) and loc.get("coords"):
            lat = float(loc["coords"].get("latitude", DEFAULT_LAT))
            lon = float(loc["coords"].get("longitude", DEFAULT_LON))
            st.sidebar.success(f"📍 Lokasi Terdeteksi: {lat:.6f}, {lon:.6f}")
        else:
            st.sidebar.warning("⚠️ Lokasi browser tidak tersedia. Gunakan input manual.")
            lat = st.sidebar.number_input("Latitude", value=DEFAULT_LAT, format="%.6f")
            lon = st.sidebar.number_input("Longitude", value=DEFAULT_LON, format="%.6f")
    except Exception:
        st.sidebar.warning("⚠️ Gagal mengambil lokasi browser. Gunakan input manual.")
        lat = st.sidebar.number_input("Latitude", value=DEFAULT_LAT, format="%.6f")
        lon = st.sidebar.number_input("Longitude", value=DEFAULT_LON, format="%.6f")
else:
    lat = st.sidebar.number_input("Latitude", value=DEFAULT_LAT, format="%.6f")
    lon = st.sidebar.number_input("Longitude", value=DEFAULT_LON, format="%.6f")

# =========================
# Prediksi Biaya (ML)
# =========================
row_sel = df[df["Penyakit"] == penyakit].iloc[0]
X_pred = pd.DataFrame([{
    "Kategori": label_encoders["Kategori"].transform([row_sel["Kategori"]])[0],
    "Penyakit": label_encoders["Penyakit"].transform([row_sel["Penyakit"]])[0],
    "Tindakan Medis Utama": label_encoders["Tindakan Medis Utama"].transform([row_sel["Tindakan Medis Utama"]])[0],
    "Estimasi Min (Rp)": row_sel["Estimasi Min (Rp)"],
    "Estimasi Max (Rp)": row_sel["Estimasi Max (Rp)"]
}])
predicted_cost = float(model.predict(X_pred)[0])

# =========================
# Hitung Jarak & Filter Radius
# =========================
pt_list = []
for idx, r in gdf_hosp.iterrows():
    try:
        p = compute_point(r.geometry, geom_method)
        d = compute_distance_km((lat, lon), (p.y, p.x))
        pt_list.append((idx, p.y, p.x, d))
    except Exception:
        continue

dist_df = pd.DataFrame(pt_list, columns=["idx", "lat", "lon", "distance_km"]).set_index("idx")
gdf_hosp2 = gdf_hosp.join(dist_df, how="inner")

nearby = gdf_hosp2[gdf_hosp2["distance_km"] <= radius_km].sort_values("distance_km")

# Pilih RS terdekat (bisa di luar radius jika radius kosong)
nearest_row = (nearby.iloc[0] if not nearby.empty else gdf_hosp2.sort_values("distance_km").iloc[0])

# =========================
# Output Teks
# =========================
st.subheader("🔍 Hasil Prediksi & Pencarian RS")
col1, col2 = st.columns(2)
with col1:
    st.write(f"🦠 **Penyakit**: {penyakit}")
    st.write(f"💰 **Estimasi Biaya (ML)**: Rp {predicted_cost:,.0f}")
    st.write(f"💵 **Budget Anda**: Rp {budget:,.0f}")
    if budget >= predicted_cost:
        st.success("✅ Budget mencukupi")
    else:
        st.warning("⚠️ Budget tidak mencukupi")

with col2:
    if not nearby.empty:
        st.write(f"🏥 **{len(nearby)} RS** dalam radius **{radius_km} km**")
    else:
        st.warning(f"⚠️ Tidak ada RS dalam radius {radius_km} km. Menampilkan RS terdekat secara global.")
    st.write(f"⭐ **RS Terdekat**: {nearest_row['NAMOBJ']} — {nearest_row['distance_km']:.2f} km")

# Tabel RS dalam radius (nama + jarak)
if not nearby.empty:
    st.dataframe(
        nearby[["NAMOBJ", "distance_km"]]
        .rename(columns={"NAMOBJ": "Rumah Sakit", "distance_km": "Jarak (km)"})
        .reset_index(drop=True)
    )

# =========================
# Peta Interaktif
# =========================
m = folium.Map(location=[lat, lon], zoom_start=12, control_scale=True)

# Marker lokasi user
folium.Marker(
    [lat, lon],
    popup="Lokasi Anda",
    icon=folium.Icon(color="red")
).add_to(m)

# Marker semua RS dalam radius (atau semua jika kosong)
plot_df = nearby if not nearby.empty else gdf_hosp2.sort_values("distance_km").head(30)

for _, r in plot_df.iterrows():
    gm_lat, gm_lon = float(r["lat"]), float(r["lon"])
    popup = folium.Popup(
        f"<b>{r['NAMOBJ']}</b><br>{r['distance_km']:.2f} km<br>"
        f'<a href="https://www.google.com/maps/dir/{lat},{lon}/{gm_lat},{gm_lon}" target="_blank">Arah (Google Maps)</a>',
        max_width=260
    )
    folium.Marker(
        [gm_lat, gm_lon],
        popup=popup,
        icon=folium.Icon(color="blue", icon="plus-sign")
    ).add_to(m)

# Garis rute sederhana ke RS terdekat
folium.PolyLine(
    [(lat, lon), (float(nearest_row["lat"]), float(nearest_row["lon"]))],
    color="green", weight=4, dash_array="6,6", opacity=0.8
).add_to(m)

# Render map
st_folium(m, width=900, height=560)

# =========================
# Catatan
# =========================
with st.expander("ℹ️ Catatan Teknis"):
    st.markdown(
        """
- Data GeoJSON difilter agar hanya menampilkan **Rumah Sakit** (menggunakan kolom **NAMOBJ/REMARK/TIPSHT**).
- Jarak dihitung dengan **geodesic** (akurasi bagus untuk jarak antar titik di bumi).
- Anda bisa memilih **metode titik geometri**:
  - **Representative Point** (default) cenderung berada di dalam poligon (baik untuk MultiPolygon).
  - **Centroid** kadang bisa berada di luar bentuk (mis. poligon cekung), tapi tetap valid untuk jarak.
- Jika radius menghasilkan nol RS, aplikasi menampilkan **RS terdekat secara global** agar tetap informatif.
- Tombol **Arah (Google Maps)** tersedia di setiap popup marker RS.
        """
    )
