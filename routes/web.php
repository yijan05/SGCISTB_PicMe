<?php

use Illuminate\Support\Facades\Route;

use App\Http\Controllers\InicioController;
use App\Http\Controllers\Auth\LoginController;
use App\Http\Controllers\Auth\RegisterController;
use App\Http\Controllers\PostController;
use App\Http\Controllers\ResenaController;
use App\Http\Controllers\ProfileController;
use App\Http\Controllers\FaceRecognitionController;


Route::get('/', [InicioController::class,'index'])->name('inicio');

//rutas de reconocimeinto facial

Route::get('/reconocimiento', [FaceRecognitionController::class, 'index'])->name('reconocimiento.index');
Route::get('/face-health', [FaceRecognitionController::class, 'health'])->name('face.health');
Route::post('/reconocer-rostro', [FaceRecognitionController::class, 'reconocer'])->name('reconocer.rostro');

#rutas protegidas pa todo lo biometrico

Route::middleware(['auth'])->group(function () {
    Route::post('/registrar-rostro', [FaceRecognitionController::class, 'registrarRostro'])->name('registrar.rostro');
    Route::post('/entrenar-modelos', [FaceRecognitionController::class, 'entrenar'])->name('entrenar.modelos');
    Route::get('/usuarios-biometricos', [FaceRecognitionController::class, 'listarUsuariosBiometricos'])->name('usuarios.biometricos');
});

#registro
Route::get('/register', [RegisterController::class, 'create'])->name('register');
Route::post('/register', [RegisterController::class, 'store'])->name('register.store');

#login
Route::get('/login', [LoginController::class, 'create'])->name('login');
Route::post('/login', [LoginController::class, 'store'])->middleware('throttle:5,1')->name('login.store');

#logout
Route::post('/logout', [LoginController::class, 'destroy'])->middleware('auth')->name('logout');

//rutas generales
Route::middleware(['auth'])->group(function () {
    Route::get('/dashboard', function(){
        return view('dashboard');
    })->name('dashboard');

    Route::post('/profile/avatar', [ProfileController::class, 'updateAvatar'])->name('profile.avatar.update');
    Route::resource('posts', PostController::class);
});

Route::post('/resenas', [ResenaController::class, 'store'])->name('resenas.store');