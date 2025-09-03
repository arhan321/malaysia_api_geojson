<?php

namespace App\Filament\Admin\Resources;

use Filament\Forms;
use Filament\Tables;
use Filament\Forms\Get;
use Filament\Forms\Form;
use Filament\Tables\Table;
use App\Models\PredictWisata;
use Filament\Resources\Resource;
use Illuminate\Support\Facades\Http;
use Filament\Forms\Components\Section;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\SoftDeletingScope;

// Tambahan import
use App\Filament\Admin\Resources\PredictWisataResource\Pages;
use App\Filament\Admin\Resources\PredictWisataResource\RelationManagers;

class PredictWisataResource extends Resource
{
    protected static ?string $model = PredictWisata::class;

    protected static ?string $navigationIcon = 'heroicon-o-rectangle-stack';

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                // === Destinasi dari /recommend ===
    //             Forms\Components\Select::make('destinasi')
    // ->label('Destinasi (hasil dari /recommend)')
    // ->placeholder('Isi Latitude & Longitude dulu…')
    // ->searchable()
    // ->reactive()
    // ->disabled(fn (Get $get) => blank($get('lat')) || blank($get('lon')))
    // ->loadingMessage('Mengambil rekomendasi…')
    // ->options(function (Get $get): array {
    //     $lat = $get('lat');
    //     $lon = $get('lon');

    //     if (blank($lat) || blank($lon)) {
    //         return [];
    //     }

    //     try {
    //         $base = rtrim(config('services.pariwisata.base_url', env('PARIWISATA_API_BASE', 'http://127.0.0.1:8000')), '/');
    //         $resp = Http::timeout(10)
    //             ->acceptJson()
    //             ->get($base . '/recommend', [
    //                 'lat'   => (float) $lat,
    //                 'lon'   => (float) $lon,
    //                 'limit' => 20,
    //             ]);

    //         if (! $resp->successful()) {
    //             return [];
    //         }

    //         $data  = $resp->json();
    //         $items = data_get($data, 'topk', []);

    //         $options = [];
    //         foreach ($items as $i => $item) {
    //             $name = data_get($item, 'name', 'Item #' . ($i + 1));
    //             $distance = data_get($item, 'distance_km');

    //             $label = $distance !== null
    //                 ? sprintf('%s — %.2f km', $name, (float) $distance)
    //                 : $name;

    //             $options[$name] = $label;
    //         }

    //         return $options;
    //     } catch (\Throwable $e) {
    //         report($e);
    //         return [];
    //     }
    // })
    // ->required(),


                Section::make('Lokasi')
                    ->schema([
                        Forms\Components\TextInput::make('lat')
                            ->label('Latitude')
                            ->numeric()
                            ->minValue(-90)->maxValue(90)
                            ->required()
                            ->reactive()
                            ->dehydrated(),

                        Forms\Components\TextInput::make('lon')
                            ->label('Longitude')
                            ->numeric()
                            ->minValue(-180)->maxValue(180)
                            ->required()
                            ->reactive()
                            ->dehydrated(),

                        Forms\Components\View::make('forms.components.ambil-lokasi'),
                    ]),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('result')
                    ->label('Destinasi'),

                Tables\Columns\TextColumn::make('lat')->label('Lat'),
                Tables\Columns\TextColumn::make('lon')->label('Lon'),
            ])
            ->filters([
                //
            ])
            ->actions([
                Tables\Actions\EditAction::make(),
            ])
            ->bulkActions([
                Tables\Actions\BulkActionGroup::make([
                    Tables\Actions\DeleteBulkAction::make(),
                ]),
            ]);
    }

    public static function getRelations(): array
    {
        return [
            //
        ];
    }

    public static function getPages(): array
    {
        return [
            'index'  => Pages\ListPredictWisatas::route('/'),
            'create' => Pages\CreatePredictWisata::route('/create'),
            'edit'   => Pages\EditPredictWisata::route('/{record}/edit'),
            'view'   => Pages\ViewPredictWisata::route('/{record}'),
        ];
    }
}
