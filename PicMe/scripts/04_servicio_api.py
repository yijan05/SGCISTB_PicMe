from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import mediapipe as mp
import numpy as np
import os
import pickle
import logging
from datetime import datetime
import joblib
from sklearn.preprocessing import StandardScaler

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# las rutas para el sistema de puntos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_MODELO_PUNTOS = os.path.join(BASE_DIR, "..", "modelos", "modelo_puntos.pkl")
RUTA_SCALER = os.path.join(BASE_DIR, "..", "modelos", "scaler.pkl")
RUTA_LABELS = os.path.join(BASE_DIR, "..", "modelos", "labels.pkl")
RUTA_PUNTOS_DATASET = os.path.join(BASE_DIR, "..", "puntos_dataset")

# umbrales ajustados para sistema de puntos
UMBRAL_CONFIANZA_PUNTOS = 0.85  # Probabilidad minima para aceptar 
UMBRAL_EAR = 0.25
PARPADEOS_NECESARIOS = 3

#aca carga los modelos
modelo_puntos = None
scaler = None
label_map = {}

def cargar_modelos():
    """Carga el modelo de puntos, scaler y labels"""
    global modelo_puntos, scaler, label_map
    
    if os.path.exists(RUTA_MODELO_PUNTOS):
        modelo_puntos = joblib.load(RUTA_MODELO_PUNTOS)
        logger.info("Modelo de puntos cargado desde %s", RUTA_MODELO_PUNTOS)
    else:
        logger.warning("No se encontro modelo en %s", RUTA_MODELO_PUNTOS)
    
    if os.path.exists(RUTA_SCALER):
        scaler = joblib.load(RUTA_SCALER)
        logger.info("Scaler cargado desde %s", RUTA_SCALER)
    
    if os.path.exists(RUTA_LABELS):
        with open(RUTA_LABELS, 'rb') as f:
            label_map = pickle.load(f)
        logger.info("Labels cargados: %s", list(label_map.values()))

#cargar al inciiar
cargar_modelos()


# cargar mediapipe solo para los puntos
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Indices de los ojos (para deteccion de parpadeo)
INDICES_OJO_IZQUIERDO = [33, 160, 158, 133, 153, 144]
INDICES_OJO_DERECHO = [362, 385, 387, 263, 373, 380]


def calcular_ear(coordenadas_ojos):
    """Calcula el Eye Aspect Ratio (EAR)"""
    try:
        a = np.linalg.norm(np.array(coordenadas_ojos[1]) - np.array(coordenadas_ojos[5]))
        b = np.linalg.norm(np.array(coordenadas_ojos[2]) - np.array(coordenadas_ojos[4]))
        c = np.linalg.norm(np.array(coordenadas_ojos[0]) - np.array(coordenadas_ojos[3]))
        ear = (a + b) / (2.0 * c)
        return ear
    except:
        return 0.0

def procesar_imagen(file_storage):
    """Convierte archivo recibido a imagen OpenCV"""
    img_bytes = file_storage.read()
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def extraer_vector_puntos(landmarks):
    """Extrae los 468 puntos 3D y los convierte en vector"""
    vector = []
    for punto in landmarks.landmark:
        vector.extend([punto.x, punto.y, punto.z])
    return np.array(vector).reshape(1, -1)

def detectar_rostro_y_puntos(img):
    """
    Detecta rostro, extrae puntos 3D y calcula parpadeos
    Retorna: (nombre, probabilidad, verificado, bbox) o (None, 0, False, None)
    """
    if modelo_puntos is None or scaler is None:
        return None, 0, False, None
    
    h, w = img.shape[:2]
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # procesar con Mediapipe, odio mediapipe, quien creo mediapupe, sera que quien lo creo se llama pipe?
    results = face_mesh.process(rgb)
    
    if not results.multi_face_landmarks:
        return None, 0, False, None
    
    landmarks = results.multi_face_landmarks[0]
    
    #prediccion inicial
    vector = extraer_vector_puntos(landmarks)
    vector_norm = scaler.transform(vector)
    
    # prediccioncon randomforest
    prediccion = modelo_puntos.predict(vector_norm)[0]
    probabilidades = modelo_puntos.predict_proba(vector_norm)[0]
    probabilidad_max = np.max(probabilidades)
    
    # determinar si es conocido
    if probabilidad_max > UMBRAL_CONFIANZA_PUNTOS and prediccion in label_map:
        nombre_detectado = label_map[prediccion]
    else:
        return None, probabilidad_max, False, None
    
    #formula de evelin

    puntos_ojo_izq = []
    puntos_ojo_der = []
    
    for idx in INDICES_OJO_IZQUIERDO:
        px = int(landmarks.landmark[idx].x * w)
        py = int(landmarks.landmark[idx].y * h)
        puntos_ojo_izq.append([px, py])
    
    for idx in INDICES_OJO_DERECHO:
        px = int(landmarks.landmark[idx].x * w)
        py = int(landmarks.landmark[idx].y * h)
        puntos_ojo_der.append([px, py])
    
    ear_izq = calcular_ear(puntos_ojo_izq)
    ear_der = calcular_ear(puntos_ojo_der)
    ear_promedio = (ear_izq + ear_der) / 2.0
    
    
    verificado = ear_promedio > UMBRAL_EAR 
    
    # esto no estoy seguro que es, no me ejecutaba y chat dijo que lo necesitaba (recodatorio para estudiar esto)
    x_coords = [int(p.x * w) for p in landmarks.landmark]
    y_coords = [int(p.y * h) for p in landmarks.landmark]
    x_min, x_max = min(x_coords), max(x_coords)
    y_min, y_max = min(y_coords), max(y_coords)
    bbox = (x_min, y_min, x_max - x_min, y_max - y_min)
    
    return nombre_detectado, probabilidad_max, verificado, bbox

# endpoint del api

@app.route('/health', methods=['GET'])
def health():
    """Verificar que el servicio esta activo"""
    return jsonify({
        'status': 'ok',
        'modelo_puntos_cargado': modelo_puntos is not None,
        'scaler_cargado': scaler is not None,
        'usuarios_registrados': list(label_map.values()) if label_map else []
    })

@app.route('/reconocer', methods=['POST'])
def reconocer():
    """
    Endpoint para reconocimiento facial basado en PUNTOS 3D
    Recibe: imagen en campo 'foto' (multipart/form-data)
    Retorna: usuario reconocido o null
    """
    try:
        # validar que llego una imagen
        if 'foto' not in request.files:
            logger.warning("Peticion sin archivo de foto")
            return jsonify({'error': 'No se envio foto'}), 400
        
        file = request.files['foto']
        
        if file.filename == '':
            logger.warning("Archivo vacio")
            return jsonify({'error': 'Archivo vacio'}), 400
        
        # procesar la imagen en general
        img = procesar_imagen(file)
        if img is None:
            logger.warning("No se pudo decodificar la imagen")
            return jsonify({'error': 'Formato de imagen invalido'}), 400
        
        # detectar rostro y puntos
        nombre, probabilidad, verificado, bbox = detectar_rostro_y_puntos(img)
        
        if nombre and verificado:
            logger.info(f"Reconocido: {nombre} (probabilidad: {probabilidad:.3f})")
            return jsonify({
                'success': True,
                'usuario': nombre,
                'probabilidad': probabilidad,
                'verificado': True,
                'bbox': bbox
            })
        elif nombre and not verificado:
            logger.info(f"Reconocido pero no verificado: {nombre}")
            return jsonify({
                'success': False,
                'usuario': nombre,
                'probabilidad': probabilidad,
                'verificado': False,
                'mensaje': 'No se pudo verificar que sea una persona real'
            })
        else:
            logger.info("Rostro no reconocido")
            return jsonify({
                'success': False,
                'usuario': None,
                'probabilidad': probabilidad if probabilidad else 0,
                'mensaje': 'Rostro no reconocido'
            })
            
    except Exception as e:
        logger.error(f"Error en reconocimiento: {str(e)}", exc_info=True)
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/registrar', methods=['POST'])
def registrar():
    """
    Endpoint para registrar puntos 3D de un nuevo usuario
    Recibe: imagen + nombre_usuario
    """
    try:
        if 'foto' not in request.files:
            return jsonify({'error': 'No se envio foto'}), 400
        
        nombre = request.form.get('nombre')
        if not nombre:
            return jsonify({'error': 'Se requiere nombre de usuario'}), 400
        
        nombre = nombre.strip().lower()
        file = request.files['foto']
        
        img = procesar_imagen(file)
        if img is None:
            return jsonify({'error': 'Imagen invalida'}), 400
        
        # extraer puntos otra vez
        h, w = img.shape[:2]
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)
        
        if not results.multi_face_landmarks:
            return jsonify({'error': 'No se detecto rostro en la imagen'}), 400
        
        landmarks = results.multi_face_landmarks[0]
        vector = extraer_vector_puntos(landmarks)
        
        # Crear la carpeta
        carpeta_usuario = os.path.join(RUTA_PUNTOS_DATASET, nombre)
        os.makedirs(carpeta_usuario, exist_ok=True)
        
        # gardar vector con puntos
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"puntos_{timestamp}.pkl"
        filepath = os.path.join(carpeta_usuario, filename)
        
        with open(filepath, 'wb') as f:
            pickle.dump({
                'vector': vector.flatten(),
                'timestamp': timestamp,
                'nombre': nombre
            }, f)
        
        logger.info(f"Puntos guardados para {nombre}: {filename}")
        
        return jsonify({
            'success': True,
            'mensaje': f'Puntos 3D guardados para {nombre}',
            'archivo': filename
        })
        
    except Exception as e:
        logger.error(f"Error en registro: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/entrenar', methods=['POST'])
def entrenar():
    """
    Endpoint para entrenar/actualizar el modelo de puntos
    """
    try:
        import subprocess
        import sys
        
        # ruta al script de entrenamiento de puntos
        script_path = os.path.join(BASE_DIR, "02_entrenar_puntos.py")
        
        if not os.path.exists(script_path):
            return jsonify({'error': 'Script de entrenamiento no encontrado'}), 500
        
        # ejecutar script de entrenamiento
        logger.info("Iniciando entrenamiento de puntos...")
        result = subprocess.run([sys.executable, script_path], 
                               capture_output=True, text=True)
        
        if result.returncode == 0:
            # Recargar modelo
            cargar_modelos()
            
            logger.info("Entrenamiento completado exitosamente")
            return jsonify({
                'success': True,
                'mensaje': 'Modelo de puntos entrenado correctamente',
                'output': result.stdout
            })
        else:
            logger.error(f"Error en entrenamiento: {result.stderr}")
            return jsonify({
                'success': False,
                'mensaje': 'Error en entrenamiento',
                'error': result.stderr
            }), 500
            
    except Exception as e:
        logger.error(f"Error al entrenar: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/usuarios', methods=['GET'])
def listar_usuarios():
    """Lista los usuarios registrados en el dataset de puntos"""
    try:
        if not os.path.exists(RUTA_PUNTOS_DATASET):
            return jsonify({'usuarios': []})
        
        usuarios = [d for d in os.listdir(RUTA_PUNTOS_DATASET) 
                   if os.path.isdir(os.path.join(RUTA_PUNTOS_DATASET, d))]
        
        # contar puntos por usuario
        resultado = []
        for usuario in usuarios:
            carpeta = os.path.join(RUTA_PUNTOS_DATASET, usuario)
            puntos = len([f for f in os.listdir(carpeta) if f.endswith('.pkl')])
            resultado.append({
                'nombre': usuario,
                'puntos': puntos
            })
        
        return jsonify({
            'success': True,
            'usuarios': resultado
        })
        
    except Exception as e:
        logger.error(f"Error listando usuarios: {str(e)}")
        return jsonify({'error': str(e)}), 500
# aca inicia el servidor, tengo un mlprido sueño, me quiero matar, que cajaros hago haciendo esto en lugar de dormir
if __name__ == '__main__':
    print("="*60)
    print("SERVICIO PICME - API DE RECONOCIMIENTO POR PUNTOS 3D")
    print("="*60)
    print(f"Dataset de puntos: {RUTA_PUNTOS_DATASET}")
    print(f"Modelo de puntos: {RUTA_MODELO_PUNTOS}")
    print(f"Usuarios registrados: {list(label_map.values()) if label_map else 'Ninguno'}")
    print("="*60)
    print("Endpoints disponibles:")
    print("  GET  /health           - Verificar estado")
    print("  POST /reconocer        - Reconocer rostro por puntos 3D")
    print("  POST /registrar        - Registrar puntos 3D de nuevo usuario")
    print("  POST /entrenar         - Entrenar modelo de puntos")
    print("  GET  /usuarios         - Listar usuarios")
    print("="*60)
    print("Servidor iniciado en http://localhost:5000")
    print("Presiona CTRL+C para detener")
    print("="*60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)