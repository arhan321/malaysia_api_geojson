<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;

class ApiKeyMiddleware
{
    public function handle(Request $request, Closure $next)
    {
        $apiKey = env('API_KEY');
        $requestApiKey = $request->header('X-API-KEY');

        if (!$requestApiKey || $requestApiKey !== $apiKey) {
            return response()->json([
                'status' => 'error',
                'message' => 'Unauthorized. Invalid API Key.'
            ], 401);
        }

        return $next($request);
    }
}
