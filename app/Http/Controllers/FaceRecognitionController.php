<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Auth;
use App\Models\User;
use App\Models\AccessLog;
use Illuminate\Support\Facades\Log;

class FaceRecognitionController extends Controller
{
    protected $pythonServiceUrl;

    public function __construct()
    {
        $this->pythonServiceUrl = env('PYTHON_SERVICE_URL', 'http://127.0.0.1:5000');
    }

    public function index()
    {
        return view('auth.reconocimiento');
    }

    public function health()
    {
        try {
            $response = Http::timeout(5)->get($this->pythonServiceUrl . '/health');
            
            if ($response->successful()) {
                return response()->json([
                    'success' => true,
                    'data' => $response->json()
                ]);
            }
            
            return response()->json([
                'success' => false,
                'message' => 'Servicio Python no disponible'
            ], 503);

        } catch (\Exception $e) {
            Log::error('Error conectando a Python: ' . $e->getMessage());
            return response()->json([
                'success' => false,
                'message' => 'No se pudo conectar al servicio de reconocimiento facial'
            ], 503);
        }
    }

    public function reconocer(Request $request)
    {
        $request->validate([
            'foto' => 'required|image|mimes:jpeg,png,jpg|max:5120'
        ]);

        try {
            $response = Http::timeout(30)
                ->attach(
                    'foto',
                    file_get_contents($request->file('foto')->path()),
                    'rostro.jpg'
                )
                ->post($this->pythonServiceUrl . '/reconocer');

            if ($response->failed()) {
                Log::error('Error en servicio Python: ' . $response->body());
                return response()->json([
                    'success' => false,
                    'message' => 'Error en el servicio de reconocimiento'
                ], 500);
            }

            $data = $response->json();

            if ($data['success'] ?? false) {
                $user = User::where('name', $data['usuario'])->first();

                if ($user) {
                    Auth::login($user);
                    $request->session()->regenerate();

                    AccessLog::create([
                        'user_id' => $user->id,
                        'evento' => 'ingreso_facial',
                        'metodo' => 'one_class_svm',
                        'confianza' => $data['confianza'] ?? null,
                        'ip_address' => $request->ip(),
                        'user_agent' => $request->userAgent()
                    ]);

                    $user->ultimo_acceso_facial = now();
                    $user->save();

                    return response()->json([
                        'success' => true,
                        'message' => '¡Bienvenido ' . $user->name . '!',
                        'redirect' => route('dashboard')
                    ]);
                } else {
                    Log::warning('Usuario reconocido pero no encontrado en BD: ' . $data['usuario']);
                }
            }

            $mensaje = $data['mensaje'] ?? 'Rostro no reconocido';
            return response()->json([
                'success' => false,
                'message' => $mensaje
            ]);

        } catch (\Exception $e) {
            Log::error('Excepcion en reconocimiento facial: ' . $e->getMessage());
            return response()->json([
                'success' => false,
                'message' => 'Error al procesar la imagen'
            ], 500);
        }
    }

    public function registrarRostro(Request $request)
    {
        $request->validate([
            'foto' => 'required|image|max:5120',
            'user_id' => 'required|exists:users,id'
        ]);

        try {
            $user = User::find($request->user_id);

            $response = Http::timeout(30)
                ->attach(
                    'foto',
                    file_get_contents($request->file('foto')->path()),
                    'rostro.jpg'
                )
                ->post($this->pythonServiceUrl . '/registrar', [
                    'nombre' => $user->name
                ]);

            if ($response->successful() && ($response->json()['success'] ?? false)) {
                $user->rostro_registrado = true;
                $user->save();

                AccessLog::create([
                    'user_id' => $user->id,
                    'evento' => 'registro_facial',
                    'metodo' => 'one_class_svm',
                    'ip_address' => $request->ip(),
                    'user_agent' => $request->userAgent()
                ]);

                return response()->json([
                    'success' => true,
                    'message' => 'Rostro registrado exitosamente'
                ]);
            }

            Log::error('Error en registro facial: ' . $response->body());
            return response()->json([
                'success' => false,
                'message' => 'Error al registrar rostro'
            ], 500);

        } catch (\Exception $e) {
            Log::error('Error en registro facial: ' . $e->getMessage());
            return response()->json([
                'success' => false,
                'message' => 'Error al conectar con servicio de reconocimiento'
            ], 500);
        }
    }

    public function entrenar()
    {
        try {
            $response = Http::timeout(300)
                ->post($this->pythonServiceUrl . '/entrenar');

            if ($response->successful()) {
                return response()->json([
                    'success' => true,
                    'message' => 'Modelos entrenados correctamente',
                    'output' => $response->json()
                ]);
            }

            return response()->json([
                'success' => false,
                'message' => 'Error en entrenamiento'
            ], 500);

        } catch (\Exception $e) {
            Log::error('Error en entrenamiento: ' . $e->getMessage());
            return response()->json([
                'success' => false,
                'message' => 'Error al conectar con servicio de entrenamiento'
            ], 500);
        }
    }

    public function listarUsuariosBiometricos()
    {
        try {
            $response = Http::timeout(10)->get($this->pythonServiceUrl . '/usuarios');

            if ($response->successful()) {
                return response()->json($response->json());
            }

            return response()->json([
                'success' => false,
                'usuarios' => []
            ]);

        } catch (\Exception $e) {
            Log::error('Error listando usuarios biometricos: ' . $e->getMessage());
            return response()->json([
                'success' => false,
                'usuarios' => []
            ], 503);
        }
    }
}