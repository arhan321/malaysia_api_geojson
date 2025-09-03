<?php

namespace App\Filament\Admin\Resources\PredictWisataResource\Pages;

use Filament\Actions;
use Illuminate\Support\Facades\Http;
use Filament\Notifications\Notification;
use Filament\Resources\Pages\CreateRecord;
use App\Filament\Admin\Resources\PredictWisataResource;

class CreatePredictWisata extends CreateRecord
{
    protected static string $resource = PredictWisataResource::class;

    protected function afterCreate(): void
    {
        $record = $this->record;

        try {
            $response = Http::withHeaders([
                'X-API-Key' => env('API_KEY', 'secret123'),
            ])->acceptJson()->get(env('PREDICT_URL', 'http://pariwisata-api:8000') . '/recommend', [
                'lat' => $record->lat,
                'lon' => $record->lon,
                //'limit' => 10, // opsional, kalau endpoint support
            ]);

            if ($response->successful()) {
                // Simpan hasil response ke kolom "result"
                $record->result = $response->json();
                $record->save();
            } else {
                \Log::error('FastAPI error', ['body' => $response->body()]);

                Notification::make()
                    ->title('Gagal memproses rekomendasi')
                    ->body($response->body())
                    ->danger()
                    ->send();
            }
        } catch (\Exception $e) {
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
