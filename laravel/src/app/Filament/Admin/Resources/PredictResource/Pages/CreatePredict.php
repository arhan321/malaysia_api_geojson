<?php

namespace App\Filament\Admin\Resources\PredictResource\Pages;

use App\Filament\Admin\Resources\PredictResource;
use Filament\Resources\Pages\CreateRecord;
use Illuminate\Support\Facades\Http;
use Filament\Notifications\Notification;

class CreatePredict extends CreateRecord
{
    protected static string $resource = PredictResource::class;

    protected function afterCreate(): void
    {
        $record = $this->record;

        try {
            $response = Http::withHeaders([
                'X-API-Key' => env('PREDICT_KEY', 'berapaya'),
            ])->asJson()->post(env('PREDICT_URL', 'http://100.100.55.20:7000') . '/predict-nearby', [
                'penyakit' => $record->penyakit,
                'budget' => $record->budget,    
                'lat' => $record->lat,
                'lon' => $record->lon,
                'radius_km' => 10,
                'geom_method' => 'Centroid',
            ]);

            if ($response->successful()) {
                $record->result = $response->json();
                $record->save();
            } else {
                // Log error
                \Log::error('FastAPI error', ['body' => $response->body()]);

                // Tampilkan notifikasi ke user
                Notification::make()
                    ->title('Gagal memproses prediksi')
                    ->body($response->body())
                    ->danger()
                    ->send();
            }
        } catch (\Exception $e) {
            // Log exception
            \Log::error('Exception saat call FastAPI', [
                'message' => $e->getMessage(),
            ]);

            Notification::make()
                ->title('Error Exception')
                ->body($e->getMessage())
                ->danger()
                ->send();
        }
    }
}
