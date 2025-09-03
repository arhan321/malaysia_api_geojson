<?php

namespace App\Livewire;

use Livewire\Component;

class LokasiPeta extends Component
{
    public $lat = -6.2;   // default Jakarta
    public $lon = 106.8;

    public function mount($lat = null, $lon = null)
    {
        if ($lat) $this->lat = $lat;
        if ($lon) $this->lon = $lon;
    }

    public function render()
    {
        return view('livewire.lokasi-peta');
    }
}
