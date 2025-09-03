import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from streamlit_javascript import st_javascript
from geopy.distance import geodesic
from shapely.geometry import Point

# Judul aplikasi
st.title("Peta Data Pariwisata")

# Load data GeoJSON
geojson_path = "mapsjatebg.geojson"
gdf = gpd.read_file(geojson_path)

# Buat geometry dari kolom x dan y jika ada
if "x" in gdf.columns and "y" in gdf.columns:
    gdf["geometry"] = gdf.apply(lambda row: Point(row["x"], row["y"]), axis=1)
    gdf = gpd.GeoDataFrame(gdf, geometry="geometry", crs="EPSG:4326")

# Sidebar untuk filter nama objek
st.sidebar.header("Filter Data")
all_names = gdf["nama_objek"].dropna().unique().tolist()
selected_name = st.sidebar.selectbox("Pilih Nama Objek", ["Semua"] + all_names)

# Filter data berdasarkan pilihan
if selected_name != "Semua":
    gdf_filtered = gdf[gdf["nama_objek"] == selected_name]
else:
    gdf_filtered = gdf

# Menampilkan data dalam tabel tanpa kolom geometry
st.subheader("Data Pariwisata")
st.dataframe(gdf_filtered.drop(columns="geometry"))

# Ambil lokasi terkini dari browser
loc = st_javascript("""
new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(
        (pos) => {
            resolve({latitude: pos.coords.latitude, longitude: pos.coords.longitude});
        },
        (err) => {
            resolve(null);
        }
    );
});
""")

# Input lokasi manual di sidebar
st.sidebar.subheader("Tentukan Lokasi Anda")
manual_lat = st.sidebar.number_input("Latitude", value=-7.4, format="%.6f")
manual_lon = st.sidebar.number_input("Longitude", value=110.3, format="%.6f")
use_manual = st.sidebar.checkbox("Gunakan lokasi manual", value=False)

# Tentukan lokasi awal
if use_manual:
    start_coords = [manual_lat, manual_lon]
    user_lat, user_lon = manual_lat, manual_lon
elif isinstance(loc, dict) and "latitude" in loc and "longitude" in loc:
    user_lat = loc["latitude"]
    user_lon = loc["longitude"]
    start_coords = [user_lat, user_lon]
else:
    start_coords = [-7.4, 110.3]
    user_lat, user_lon = start_coords

# Buat peta dasar
m = folium.Map(location=start_coords, zoom_start=13, tiles="CartoDB positron")

# Tandai lokasi pengguna
folium.Marker(
    location=[user_lat, user_lon],
    popup="Lokasi Anda",
    icon=folium.Icon(color="red", icon="user")
).add_to(m)

# Hitung jarak ke semua objek wisata
if "x" in gdf_filtered.columns and "y" in gdf_filtered.columns:
    gdf_coords = gdf_filtered.copy()
    gdf_coords["distance"] = gdf_coords.apply(
        lambda row: geodesic(
            (user_lat, user_lon),
            (row["y"], row["x"])
        ).kilometers,
        axis=1
    )

    # Ambil 3 objek wisata terdekat
    rekomendasi = gdf_coords.nsmallest(3, "distance")

    st.subheader("Rekomendasi Pariwisata Terdekat (CBF)")
    st.dataframe(rekomendasi[["nama_objek", "jenis_obje", "alamat", "distance"]])

    # Tambahkan marker dan jalur untuk rekomendasi
    for _, row in rekomendasi.iterrows():
        # Marker objek wisata
        folium.Marker(
            location=[row["y"], row["x"]],
            popup=f"{row['nama_objek']} ({row['distance']:.2f} km)",
            icon=folium.Icon(color="green", icon="star")
        ).add_to(m)

        # Jalur garis lurus dari lokasi user ke objek wisata
        folium.PolyLine(
            locations=[[user_lat, user_lon], [row["y"], row["x"]]],
            color="blue",
            weight=2,
            opacity=0.7,
            dash_array="5, 10"
        ).add_to(m)

# Pilih hanya kolom non-geometry untuk tooltip
tooltip_fields = [col for col in gdf.columns if col != "geometry"]

# Tambahkan layer GeoJSON dengan tooltip
folium.GeoJson(
    gdf_filtered,
    name="Pariwisata",
    tooltip=folium.GeoJsonTooltip(
        fields=tooltip_fields,
        aliases=tooltip_fields,
        localize=True
    )
).add_to(m)

# Tambahkan kontrol layer
folium.LayerControl().add_to(m)

# Tampilkan peta di Streamlit
st.subheader("Peta Interaktif")
st_folium(m, width=800, height=500)