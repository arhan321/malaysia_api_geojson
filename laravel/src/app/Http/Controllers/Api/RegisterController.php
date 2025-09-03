<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\Validator;
use App\Models\User;
use App\Helpers\EncryptionHelper;
use Exception;

class RegisterController extends Controller
{
    public function register(Request $request)
    {
        try {
            // Validasi input
            $validator = Validator::make($request->all(), [
                'name'     => 'required|string|max:255',
                'email'    => 'required|email|unique:users,email',
                'password' => 'required|string|min:6|confirmed', // password_confirmation wajib
            ]);

            if ($validator->fails()) {
                return response()->json([
                    'status'  => 'error',
                    'message' => 'Validation failed',
                    'errors'  => $validator->errors(),
                ], 400);
            }

            // Simpan user baru
            $user = User::create([
                'name'     => $request->name,
                'email'    => $request->email,
                'password' => Hash::make($request->password),
            ]);

            $userData = [
                'id'    => $user->id,
                'name'  => $user->name,
                'email' => $user->email,
            ];

            // Encrypt response (opsional)
            $encrypted = EncryptionHelper::encrypt(json_encode($userData));

            return response()->json([
                'status'   => 'success',
                'message'  => 'Registration successful',
                'data'     => $userData,
                'encrypted'=> $encrypted
            ], 200);

        } catch (Exception $e) {
            return response()->json([
                'status'  => 'error',
                'message' => 'Server error',
                'error'   => $e->getMessage(),
            ], 500);
        }
    }
}
