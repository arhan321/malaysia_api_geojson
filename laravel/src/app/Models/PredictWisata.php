<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Factories\HasFactory;

class PredictWisata extends Model
{
    protected $fillable = [
        //'destinasi',
        // 'budget',
        'lat',
        'lon',
        // 'radius_km',
        'result',
    ];

    protected $casts = [
        'result' => 'array',
    ];
}
