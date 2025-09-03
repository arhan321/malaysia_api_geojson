<?php

namespace App\Helpers;

use Illuminate\Support\Facades\Crypt;

class EncryptionHelper
{
    public static function encrypt($data)
    {
        return Crypt::encryptString($data);
    }

    public static function decrypt($encryptedData)
    {
        try {
            return Crypt::decryptString($encryptedData);
        } catch (\Exception $e) {
            return 'Decryption Failed: ' . $e->getMessage();
        }
    }
}
