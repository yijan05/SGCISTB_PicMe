<?php

use Illuminate\Support\Facades\Route;

use App\Http\Controllers\InicioController;
use App\Http\Controllers\Auth\LoginController;
use App\Http\Controllers\Auth\RegisterController;
use App\Http\Controllers\PostController;
use App\Http\Controllers\ResenaController;
use App\Http\Controllers\ProfileController;



Route::get('/', [InicioController::class,'index'])->name('inicio');



// registro
Route::get('/register', [RegisterController::class, 'create'])->name('register');

Route::post('/register', [RegisterController::class, 'store'])
    ->name('register.store');


// login
Route::get('/login', [LoginController::class, 'create'])
    ->name('login');

// seguridad contra ataques (5 intentos por minuto)
Route::post('/login', [LoginController::class, 'store'])
    ->middleware('throttle:5,1')
    ->name('login.store');


// logout
Route::post('/logout', [LoginController::class, 'destroy'])
    ->middleware('auth')
    ->name('logout');




Route::middleware(['auth'])->group(function () {

    Route::get('/dashboard', function(){
        return view('dashboard');
    })->name('dashboard');


    Route::post('/profile/avatar', 
        [ProfileController::class, 'updateAvatar']
    )->name('profile.avatar.update');


    // posts protegidos
    Route::resource('posts', PostController::class);

});




Route::post('/resenas', [ResenaController::class, 'store'])
    ->name('resenas.store');