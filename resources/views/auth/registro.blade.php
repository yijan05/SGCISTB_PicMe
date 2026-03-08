<!doctype html>
<html lang="es">
<head>
    @vite(['resources/css/app.css', 'resources/js/app.js'])

    <title>Registro</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;800&family=Quicksand:wght@300;500;700&family=Satisfy&display=swap" rel="stylesheet">

    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">

    <!-- Bootstrap -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
</head>

<body>

<!-- HEADER -->
<header class="container-fluid header-esmeralda d-flex justify-content-between align-items-center">
    <h1 class="mb-0">Yiyi Joyería</h1>

    <a href="{{ route('welcome') }}" class="btn-welcome">
        <img src="{{ asset('img/hom.png') }}" alt="Inicio">
    </a>
</header>

<!-- REGISTRO -->

<main class="container mt-5 mb-5">
    
    <div class="form-container mx-auto">

        <h1 class="mb-4">Registro de usuario</h1>

        <form action="{{ route('register.store') }}" method="POST">
            @csrf

            <div class="mb-3">
                <label class="form-label">Nombre del usuario</label>
                <input
                    type="text"
                    name="name"
                    class="form-control"
                    placeholder="Nombre"
                    value="{{ old('name') }}"
                    required
                >
            </div>

            <div class="mb-3">
                <label class="form-label">Correo electrónico</label>
                <input
                    type="email"
                    name="email"
                    class="form-control"
                    placeholder="Correo"
                    value="{{ old('email') }}"
                    required
                >
            </div>

            <div class="mb-3">
                <label class="form-label">Contraseña</label>
                <input
                    type="password"
                    name="password"
                    class="form-control"
                    placeholder="Contraseña"
                    required
                >
            </div>

            <div class="mb-4">
                <label class="form-label">Confirmar contraseña</label>
                <input
                    type="password"
                    name="password_confirmation"
                    class="form-control"
                    placeholder="Confirmar contraseña"
                    required
                >
            </div>

            <button type="submit" class="btn btn-primary w-100">
                Registrar
            </button>
        </form>

        {{-- ERRORES --}}
        @if ($errors->any())
            <div class="alert alert-danger mt-4">
                <ul class="mb-0">
                    @foreach ($errors->all() as $error)
                        <li>{{ $error }}</li>
                    @endforeach
                </ul>
            </div>
        @endif

    </div>
</main>

<!-- FOOTER -->
<footer class="footer-section">
    <div class="container-fluid footer-container">
        <div class="row text-start">

            <div class="col-12 col-md-6 col-lg-3 footer-col">
                <button class="footer-btn" data-bs-toggle="collapse" data-bs-target="#productos">
                    Productos de Yiyi Joyería
                </button>
                <ul id="productos" class="footer-list collapse show">
                    <li>Anillos de compromiso</li>
                    <li>Dijes</li>
                    <li>Collares</li>
                    <li>Aretes</li>
                </ul>
            </div>

            <div class="col-12 col-md-6 col-lg-3 footer-col">
                <button class="footer-btn" data-bs-toggle="collapse" data-bs-target="#info">
                    Información
                </button>
                <ul id="info" class="footer-list collapse show">
                    <li>Sobre Yiyi Joyería</li>
                    <li>Puntos de venta</li>
                    <li>Preguntas frecuentes</li>
                </ul>
            </div>

            <div class="col-12 col-md-6 col-lg-3 footer-col">
                <button class="footer-btn" data-bs-toggle="collapse" data-bs-target="#legal">
                    Información legal
                </button>
                <ul id="legal" class="footer-list collapse show">
                    <li>RUT</li>
                    <li>Cámara de Comercio</li>
                    <li>DIAN</li>
                    <li>RUCOM</li>
                </ul>
            </div>

            <div class="col-12 col-md-6 col-lg-3 footer-col">
                <button class="footer-btn" data-bs-toggle="collapse" data-bs-target="#contacto">
                    Contacto
                </button>
                <ul id="contacto" class="footer-list collapse show">
                    <li>WhatsApp</li>
                    <li>Correo</li>
                    <li>Formulario</li>
                </ul>
            </div>

        </div>
    </div>

    <div class="header-derechos text-center mt-3">
        <h6>Derechos de autor © PicMe</h6>
    </div>
</footer>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>