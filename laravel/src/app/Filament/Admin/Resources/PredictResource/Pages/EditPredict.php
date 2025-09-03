<?php

namespace App\Filament\Admin\Resources\PredictResource\Pages;

use App\Filament\Admin\Resources\PredictResource;
use Filament\Actions;
use Filament\Resources\Pages\EditRecord;

class EditPredict extends EditRecord
{
    protected static string $resource = PredictResource::class;

    protected function getHeaderActions(): array
    {
        return [
            Actions\DeleteAction::make(),
        ];
    }
}
