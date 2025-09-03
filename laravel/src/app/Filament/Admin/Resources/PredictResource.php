<?php

namespace App\Filament\Admin\Resources;

use App\Filament\Admin\Resources\PredictResource\Pages;
use App\Models\Predict;
use Filament\Forms;
use Filament\Forms\Components\Section;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;

class PredictResource extends Resource
{
    protected static ?string $model = Predict::class;

    protected static ?string $navigationIcon = 'heroicon-o-rectangle-stack';

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\TextInput::make('penyakit')
                    ->label('Penyakit')
                    ->required(),

                Forms\Components\TextInput::make('budget')
                    ->label('Budget')
                    ->numeric()
                    ->required(),

                Section::make('Lokasi')
                    ->schema([
                        Forms\Components\TextInput::make('lat')
                            ->label('Latitude')
                            ->numeric()
                            ->required()
                            ->reactive()
                            ->dehydrated(),

                        Forms\Components\TextInput::make('lon')
                            ->label('Longitude')
                            ->numeric()
                            ->required()
                            ->reactive()
                            ->dehydrated(),

                        Forms\Components\View::make('forms.components.ambil-lokasi'),
                    ]),

                // Forms\Components\TextInput::make('radius_km')
                //     ->label('Radius km')
                //     ->numeric()
                //     ->default(10),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('penyakit'),
                Tables\Columns\TextColumn::make('budget'),
                Tables\Columns\TextColumn::make('lat'),
                Tables\Columns\TextColumn::make('lon'),
                Tables\Columns\TextColumn::make('radius_km'),
                Tables\Columns\TextColumn::make('result.predicted_cost')
                    ->label('Prediksi Biaya')
                    ->numeric()
                    ->sortable(),
            ])
            ->filters([])
            ->actions([
                Tables\Actions\ViewAction::make(), // Tambahkan ViewAction
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
        return [];
    }

    public static function getPages(): array
    {
        return [
            'index'  => Pages\ListPredicts::route('/'),
            'create' => Pages\CreatePredict::route('/create'),
            'edit'   => Pages\EditPredict::route('/{record}/edit'),
            'view'   => Pages\ViewPredict::route('/{record}'),
        ];
    }
}
