<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('predicts', function (Blueprint $table) {
            $table->id();
            $table->string('penyakit');
            $table->bigInteger('budget');
            $table->decimal('lat', 10, 6);
            $table->decimal('lon', 10, 6);
            $table->integer('radius_km')->default(10);
            $table->json('result')->nullable();
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('predicts');
    }
};
