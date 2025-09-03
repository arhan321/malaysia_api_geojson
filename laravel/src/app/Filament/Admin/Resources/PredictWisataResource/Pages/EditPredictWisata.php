<?php

namespace App\Filament\Admin\Resources\PredictWisataResource\Pages;

use App\Filament\Admin\Resources\PredictWisataResource;
use Filament\Actions;
use Filament\Resources\Pages\EditRecord;

class EditPredictWisata extends EditRecord
{
    protected static string $resource = PredictWisataResource::class;

    protected function getHeaderActions(): array
    {
        return [
            Actions\DeleteAction::make(),
        ];
    }
}
