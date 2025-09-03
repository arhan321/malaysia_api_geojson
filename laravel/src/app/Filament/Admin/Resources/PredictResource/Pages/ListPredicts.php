<?php

namespace App\Filament\Admin\Resources\PredictResource\Pages;

use App\Filament\Admin\Resources\PredictResource;
use Filament\Actions;
use Filament\Resources\Pages\ListRecords;

class ListPredicts extends ListRecords
{
    protected static string $resource = PredictResource::class;

    protected function getHeaderActions(): array
    {
        return [
            Actions\CreateAction::make(),
        ];
    }
}
