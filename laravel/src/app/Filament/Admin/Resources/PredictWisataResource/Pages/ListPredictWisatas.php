<?php

namespace App\Filament\Admin\Resources\PredictWisataResource\Pages;

use App\Filament\Admin\Resources\PredictWisataResource;
use Filament\Actions;
use Filament\Resources\Pages\ListRecords;

class ListPredictWisatas extends ListRecords
{
    protected static string $resource = PredictWisataResource::class;

    protected function getHeaderActions(): array
    {
        return [
            Actions\CreateAction::make(),
        ];
    }
}
