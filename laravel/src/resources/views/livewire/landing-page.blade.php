<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Berapa Ya - Product Landing</title>
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 text-gray-900">

    <!-- Navbar -->
    <nav class="navbar navbar-expand-lg navbar-light bg-white shadow-sm">
        <div class="container">
            <a class="navbar-brand fw-bold text-xl text-blue-600" href="#">Berapa Ya</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse justify-content-end" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item"><a class="nav-link" href="#features">Features</a></li>
                    <li class="nav-item"><a class="nav-link" href="#pricing">Pricing</a></li>
                    <li class="nav-item"><a class="nav-link" href="#contact">Contact</a></li>
                </ul>
            </div>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="bg-gradient-to-r from-blue-600 to-indigo-700 text-white py-20">
        <div class="container text-center">
            <h1 class="display-4 fw-bold mb-4">Selamat Datang di <span class="text-yellow-300">Berapa Ya</span></h1>
            <p class="lead mb-5">Platform pintar untuk menghitung, membandingkan, dan mencari harga terbaik dengan cepat.</p>
            <a href="#pricing" class="btn btn-light btn-lg shadow-lg">Lihat Harga</a>
        </div>
    </section>

    <!-- Features -->
    <section id="features" class="py-16">
        <div class="container">
            <h2 class="text-3xl font-bold text-center mb-12">✨ Fitur Utama</h2>
            <div class="row g-4">
                <div class="col-md-4">
                    <div class="bg-white rounded-2xl shadow p-6 hover:shadow-lg transition">
                        <h3 class="text-xl font-semibold mb-2">🔎 Pencarian Cepat</h3>
                        <p class="text-gray-600">Cari harga produk dari berbagai sumber dalam hitungan detik.</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="bg-white rounded-2xl shadow p-6 hover:shadow-lg transition">
                        <h3 class="text-xl font-semibold mb-2">📊 Perbandingan Mudah</h3>
                        <p class="text-gray-600">Bandingkan produk secara side-by-side untuk keputusan terbaik.</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="bg-white rounded-2xl shadow p-6 hover:shadow-lg transition">
                        <h3 class="text-xl font-semibold mb-2">⚡ Real-time Update</h3>
                        <p class="text-gray-600">Harga selalu up-to-date dengan data terbaru dari marketplace.</p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Pricing -->
    <section id="pricing" class="bg-gray-50 py-16">
        <div class="container text-center">
            <h2 class="text-3xl font-bold mb-12">💰 Harga Paket</h2>
            <div class="row justify-content-center g-4">
                <div class="col-md-4">
                    <div class="bg-white rounded-2xl shadow p-6 hover:shadow-lg">
                        <h3 class="text-xl font-semibold mb-3">Gratis</h3>
                        <p class="text-4xl font-bold text-blue-600 mb-4">Rp 0</p>
                        <ul class="text-gray-600 mb-4">
                            <li>✔ 10 pencarian / hari</li>
                            <li>✔ Akses dasar</li>
                            <li>✘ Tanpa export data</li>
                        </ul>
                        <a href="#" class="btn btn-outline-primary w-100">Mulai Gratis</a>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="bg-white rounded-2xl shadow-lg border-2 border-blue-600 p-6">
                        <h3 class="text-xl font-semibold mb-3">Pro</h3>
                        <p class="text-4xl font-bold text-blue-600 mb-4">Rp 99K/bulan</p>
                        <ul class="text-gray-600 mb-4">
                            <li>✔ Unlimited pencarian</li>
                            <li>✔ Perbandingan produk</li>
                            <li>✔ Export data</li>
                        </ul>
                        <a href="#" class="btn btn-primary w-100">Pilih Paket</a>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Contact -->
    <section id="contact" class="py-16">
        <div class="container text-center">
            <h2 class="text-3xl font-bold mb-6">📩 Hubungi Kami</h2>
            <p class="text-gray-600 mb-6">Punya pertanyaan? Kami siap membantu!</p>
            <a href="mailto:support@berapaya.com" class="btn btn-success btn-lg">Email Kami</a>
        </div>
    </section>

    <!-- Footer -->
    <footer class="bg-white py-6 text-center text-gray-500 border-t">
        &copy; <span class="fw-bold">Berapa Ya</span> 2025. All Rights Reserved.
    </footer>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
