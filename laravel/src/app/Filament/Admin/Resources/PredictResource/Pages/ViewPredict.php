<?php

namespace App\Filament\Admin\Resources\PredictResource\Pages;

use App\Filament\Admin\Resources\PredictResource;
use Filament\Resources\Pages\ViewRecord;
use Filament\Infolists;
use Filament\Infolists\Components\Section;
use Filament\Infolists\Components\TextEntry;
use Filament\Infolists\Components\RepeatableEntry;

class ViewPredict extends ViewRecord
{
    protected static string $resource = PredictResource::class;

    protected function getHeaderWidgets(): array
    {
        return [];
    }

    public function infolist(Infolists\Infolist $infolist): Infolists\Infolist
    {
        return $infolist
            ->schema([
                Section::make('Detail Prediksi')
                    ->schema([
                        TextEntry::make('penyakit')->label('Penyakit'),
                        TextEntry::make('budget')->label('Budget')->money('IDR'),
                        TextEntry::make('result.predicted_cost')->label('Prediksi Biaya')->money('IDR'),
                        TextEntry::make('result.budget_ok')
                            ->label('Status Budget')
                            ->formatStateUsing(fn ($state) => $state ? '✅ OK' : '❌ Over'),
                        TextEntry::make('radius_km')->label('Radius (km)'),

                        TextEntry::make('result.note')
                            ->label('Catatan')
                            ->default('-'),
                    ])
                    ->columns(2),

                Section::make('RS Terdekat')
                    ->schema([
                        TextEntry::make('result.nearest_hospital.name')->label('Nama RS'),
                        TextEntry::make('result.nearest_hospital.distance_km')
                            ->label('Jarak (km)')
                            ->numeric(2),
                        TextEntry::make('result.nearest_hospital.google_maps_directions')
                            ->label('Google Maps')
                            ->url(fn ($state) => $state, true)
                            ->openUrlInNewTab(),
                    ])
                    ->columns(2),

                Section::make('Daftar RS dalam Radius')
                    ->schema([
                        RepeatableEntry::make('result.hospitals_in_radius')
                            ->schema([
                                TextEntry::make('name')->label('Nama RS'),
                                TextEntry::make('distance_km')
                                    ->label('Jarak (km)')
                                    ->numeric(2),
                                TextEntry::make('google_maps_directions')
                                    ->label('Google Maps')
                                    ->url(fn ($state) => $state, true)
                                    ->openUrlInNewTab(),
                            ])
                            ->columns(3),
                    ])
                    ->collapsible(),
            ]);
    }
}
