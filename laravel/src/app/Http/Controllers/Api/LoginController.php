<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Log;
use App\Helpers\EncryptionHelper;

class LoginController extends Controller
{
    public function login(Request $request)
    {
        try {
            // ✅ Validasi input
            $credentials = $request->validate([
                'email'    => 'required|email',
                'password' => 'required|string',
            ]);

            // ❌ Login gagal
            if (!Auth::attempt($credentials)) {
                return response()->json([
                    'status'  => 'error',
                    'message' => 'Invalid email or password',
                    'data'    => null,
                    'encrypted' => null
                ], 400);
            }

            // ✅ Login berhasil
            $user = Auth::user();
            $userData = [
                'id'    => $user->id,
                'name'  => $user->name,
                'email' => $user->email,
            ];

            // 🔒 Enkripsi data user
            $encryptedData = EncryptionHelper::encrypt(json_encode($userData));

            return response()->json([
                'status'    => 'success',
                'message'   => 'Login successful',
                //'data'      => $userData,
                'data' => $encryptedData
            ], 200);

        } catch (\Illuminate\Validation\ValidationException $e) {
            // ⚠️ Error validasi
            return response()->json([
                'status'  => 'error',
                'message' => 'Validation failed',
                'errors'  => $e->errors(),
                'data'    => null,
                'encrypted' => null
            ], 400);

        } catch (\Exception $e) {
            // 💥 Error server
            Log::error("Login error: " . $e->getMessage());

            return response()->json([
                'status'  => 'error',
                'message' => 'Internal Server Error',
                'data'    => null,
                'encrypted' => null
            ], 500);
        }
    }
}
