@once
    {{-- Leaflet CSS & JS --}}
    <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
@endonce

<div x-data="mapLokasi()" x-init="init()">
    <div class="mb-2">
        <button
            type="button"
            class="px-4 py-2 bg-blue-600 text-white rounded-md"
            @click="ambilLokasi()"
        >
            📍 Ambil Lokasi Sekarang
        </button>
    </div>

    {{-- Peta --}}
    {{-- <div id="map" style="height: 300px;" class="rounded-md shadow"></div> --}}

    <script>
        document.addEventListener("alpine:init", () => {
            Alpine.data("mapLokasi", () => ({
                map: null,
                marker: null,

                init() {
                    let lat = this.$wire.entangle('data.lat').live || -6.2
                    let lon = this.$wire.entangle('data.lon').live || 106.8

                    this.map = L.map("map").setView([lat, lon], 12)

                    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
                        attribution: "© OpenStreetMap contributors"
                    }).addTo(this.map)

                    this.marker = L.marker([lat, lon], { draggable: true }).addTo(this.map)

                    this.marker.on("moveend", (e) => {
                        this.$wire.set("data.lat", e.target.getLatLng().lat)
                        this.$wire.set("data.lon", e.target.getLatLng().lng)
                    })

                    this.map.on("click", (e) => {
                        this.marker.setLatLng(e.latlng)
                        this.$wire.set("data.lat", e.latlng.lat)
                        this.$wire.set("data.lon", e.latlng.lng)
                    })

                    // fix ukuran tile
                    setTimeout(() => {
                        this.map.invalidateSize()
                    }, 500)
                },

                ambilLokasi() {
                    if (navigator.geolocation) {
                        navigator.geolocation.getCurrentPosition(
                            (pos) => {
                                let lat = pos.coords.latitude
                                let lon = pos.coords.longitude
                                this.$wire.set("data.lat", lat)
                                this.$wire.set("data.lon", lon)

                                this.map.setView([lat, lon], 15)
                                this.marker.setLatLng([lat, lon])
                            },
                            (err) => alert("Gagal ambil lokasi: " + err.message)
                        )
                    } else {
                        alert("Browser tidak mendukung Geolocation")
                    }
                }
            }))
        })
    </script>
</div>
