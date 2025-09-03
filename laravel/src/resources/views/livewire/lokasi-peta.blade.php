@once
    <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
@endonce

<div x-data="mapLokasi()" x-init="init()" class="space-y-3">
    <button
        type="button"
        class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg shadow
               hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-400 transition"
        @click="ambilLokasi()"
    >
        <span>📍</span> Ambil Lokasi Sekarang
    </button>

    <div id="map" style="height: 350px;" class="rounded-lg shadow border"></div>

    <script>
        document.addEventListener("alpine:init", () => {
            Alpine.data("mapLokasi", () => ({
                map: null,
                marker: null,
                latModel: @entangle('lat').defer,
                lonModel: @entangle('lon').defer,

                init() {
                    let lat = this.latModel || -6.2
                    let lon = this.lonModel || 106.8

                    if (this.map) return

                    this.map = L.map("map").setView([lat, lon], 12)

                    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
                        attribution: "© OpenStreetMap contributors"
                    }).addTo(this.map)

                    this.marker = L.marker([lat, lon], { draggable: true }).addTo(this.map)

                    this.marker.on("moveend", (e) => {
                        this.latModel = e.target.getLatLng().lat
                        this.lonModel = e.target.getLatLng().lng
                    })

                    this.map.on("click", (e) => {
                        this.marker.setLatLng(e.latlng)
                        this.latModel = e.latlng.lat
                        this.lonModel = e.latlng.lng
                    })

                    setTimeout(() => this.map.invalidateSize(), 400)
                },

                ambilLokasi() {
                    if (navigator.geolocation) {
                        navigator.geolocation.getCurrentPosition(
                            (pos) => {
                                let lat = pos.coords.latitude
                                let lon = pos.coords.longitude
                                this.latModel = lat
                                this.lonModel = lon
                                this.map.setView([lat, lon], 15)
                                this.marker.setLatLng([lat, lon])
                            },
                            (err) => alert("❌ Gagal ambil lokasi: " + err.message)
                        )
                    } else {
                        alert("⚠️ Browser tidak mendukung Geolocation")
                    }
                }
            }))
        })
    </script>
</div>
