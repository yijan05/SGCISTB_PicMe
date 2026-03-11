<!DOCTYPE html>
<html lang="es">
<head>

@vite(['resources/css/app.css', 'resources/js/app.js'])
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Nunito:ital,wght@0,200..1000;1,200..1000&display=swap" rel="stylesheet">

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,100..900;1,100..900&family=Quicksand:wght@300..700&display=swap" rel="stylesheet">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inconsolata:wght@500&display=swap" rel="stylesheet">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inconsolata:wght@500&family=Satisfy&display=swap" rel="stylesheet">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inconsolata:wght@500&family=Playfair+Display:ital,wght@0,400..900;1,400..900&family=Satisfy&display=swap" rel="stylesheet">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inconsolata:wght@500&family=Playfair+Display:ital,wght@0,400..900;1,400..900&family=Quicksand:wght@300..700&family=Satisfy&display=swap" rel="stylesheet">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@300..700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>PicMe - Reconocimiento Facial</title>

<link rel="stylesheet" href="styles.css">

</head>
<body>

<!-- PANTALLA DE CARGA -->
<div id="loading-screen">

    <video autoplay muted loop id="loading-video">
        <source src="{{ asset('img/logo_animado.mp4') }}" type="video/mp4">
    </video>

    <button id="btn-comenzar" onclick="mostrarMenu()">
        Comenzar
    </button>

</div>


<!-- CONTENEDOR PRINCIPAL -->
<div class="contenedor-principal" id="menu">

    <!-- PANEL IZQUIERDO -->
    <div class="panel-izquierdo">

        <div class="contenido-izquierdo">

            <h2>Universidad de Cundinamarca</h2>

            <img src="{{ asset('img/ubate.png') }}" alt="Universidad">

            <p>
                Sistema PicMe  
                Reconocimiento facial para control y registro de usuarios
            </p>

        </div>

    </div>


    <!-- PANEL DERECHO -->
    <div class="panel-derecho">

        <div class="login-box">

            <h1 class="titulo-picme"><img src="{{ asset('img/picm.png') }}" alt="Universidad"></h1>

            <p>Reconocimiento Facial</p>

            <form action="/face-login" method ="POST" enctype="multipart/form-data">
                @csrf
                <input type="file" name="foto" required>
                <button> class="btn-principal" type="submit"
                    reconocer rostor
                </button>

            </form>

            <br>

            <!-- el boton de registro -->

            <input type="email" placeholder="Correo electrónico">

            <input type="password" placeholder="Contraseña">


            <button class="btn-principal" onclick="iniciarSesion()">
                Iniciar Sesión
            </button>


            <button class="btn-secundario" onclick="registrarUsuario()">
                Registrar Usuario
            </button>


        </div>

    </div>

</div>



<script>

function mostrarMenu(){
document.getElementById("loading-screen").style.display="none";
document.getElementById("menu").style.display="flex";
}


function registrarUsuario(){
window.location.href="registro.html";
}

</script>


</body>
</html>