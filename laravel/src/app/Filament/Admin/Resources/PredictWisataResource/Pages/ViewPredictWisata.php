<?php

namespace App\Filament\Admin\Resources\PredictWisataResource\Pages;

use Filament\Infolists\Infolist;
use Filament\Resources\Pages\ViewRecord;
use Filament\Infolists\Components\TextEntry;
use Filament\Infolists\Components\RepeatableEntry;
use Filament\Infolists\Components\Section as InfoSection;
use App\Filament\Admin\Resources\PredictWisataResource;

class ViewPredictWisata extends ViewRecord
{
    protected static string $resource = PredictWisataResource::class;

    public function infolist(Infolist $infolist): Infolist
    {
        return $infolist
            ->schema([
                InfoSection::make('Lokasi User')
                    ->schema([
                        TextEntry::make('lat')->label('Latitude'),
                        TextEntry::make('lon')->label('Longitude'),
                    ]),

                InfoSection::make('Rekomendasi Terdekat')
                    ->schema([
                        RepeatableEntry::make('result.topk') // akses array di JSON result
                            ->label('Top-K Destinasi')
                            ->schema([
                                TextEntry::make('name')->label('Nama Destinasi'),
                                TextEntry::make('latitude')->label('Lat'),
                                TextEntry::make('longitude')->label('Lon'),
                                TextEntry::make('distance_km')
                                    ->label('Jarak (km)')
                                    ->formatStateUsing(fn ($state) => number_format((float) $state, 2) . ' km'),
                            ]),
                    ]),
            ]);
    }
}
