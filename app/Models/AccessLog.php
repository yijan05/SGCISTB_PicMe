<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class AccessLog extends Model
{
    use HasFactory;

    protected $fillable = [
        'user_id',
        'evento',
        'metodo',
        'confianza',
        'ip_address',
        'user_agent'
    ];

    protected $casts = [
        'confianza' => 'float',
    ];

    public function user()
    {
        return $this->belongsTo(User::class);
    }
}