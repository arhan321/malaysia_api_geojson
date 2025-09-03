<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Predict extends Model
{
    protected $fillable = [
        'penyakit',
        'budget',
        'lat',
        'lon',
        'radius_km',
        'result',
    ];

    protected $casts = [
        'result' => 'array',
    ];
}
