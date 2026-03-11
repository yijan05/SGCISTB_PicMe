import cv2
import mediapipe as mp
import os
import time
import numpy as np
import pickle
from datetime import datetime

RUTA_BASE_DATASET = "C:/Users/jvier/OneDrive - UNIVERSIDAD DE CUNDINAMARCA/EVELIN YIJAN VIRGUEZ PARRA's files - PicMe/Códigos/2026-1/dataset"
RUTA_PUNTOS_DATASET = "C:/Users/jvier/OneDrive - UNIVERSIDAD DE CUNDINAMARCA/EVELIN YIJAN VIRGUEZ PARRA's files - PicMe/Códigos/2026-1/puntos_dataset"  
NUM_FOTOS_POR_POSICION = 10   
PAUSA_ENTRE_FOTOS = 0.3      
UMBRAL_EAR = 0.25             
PARPADEOS_NECESARIOS = 10  

# Crear carpeta para puntos si no existe
os.makedirs(RUTA_PUNTOS_DATASET, exist_ok=True)

# aca seria el analisis para la facil mesh de mediapipe
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# indices para saber hacia donde esta apuntando la gta
INDICE_NARIZ = 1
INDICE_FRENTE = 10
INDICE_BARBILLA = 152
INDICE_MEJILLA_IZQ = 234
INDICE_MEJILLA_DER = 454

# indices de los ojos para la formula esa de evelin
INDICES_OJO_IZQUIERDO = [33, 160, 158, 133, 153, 144]
INDICES_OJO_DERECHO = [362, 385, 387, 263, 373, 380]

def calcular_ear(coordenadas_ojos):
    """
    Calcula el Eye Aspect Ratio (EAR)
    Formula: EAR = (|p2-p6| + |p3-p5|) / (2 * |p1-p4|)
    """
    try:
        a = np.linalg.norm(np.array(coordenadas_ojos[1]) - np.array(coordenadas_ojos[5]))
        b = np.linalg.norm(np.array(coordenadas_ojos[2]) - np.array(coordenadas_ojos[4]))
        c = np.linalg.norm(np.array(coordenadas_ojos[0]) - np.array(coordenadas_ojos[3]))
        
        ear = (a + b) / (2.0 * c)
        return ear
    except:
        return 0.0

def extraer_vector_puntos(landmarks):
    """
    Convierte los 468 puntos 3D en un vector de caracteristicas
    """
    vector = []
    for punto in landmarks.landmark:
        vector.append(punto.x)  # coordenada x
        vector.append(punto.y)  # coordenada y
        vector.append(punto.z)  # coordenada z (profundidad)
    return np.array(vector)

def alinear_rostro(imagen, landmarks):
    """
    Alinea el rostro usando los ojos como referencia
    """
    # Obtener coordenadas de los ojos
    ojo_izq_x = landmarks.landmark[33].x
    ojo_izq_y = landmarks.landmark[33].y
    ojo_der_x = landmarks.landmark[263].x
    ojo_der_y = landmarks.landmark[263].y
    
    h, w = imagen.shape[:2]
    ojo_izq = np.array([ojo_izq_x * w, ojo_izq_y * h])
    ojo_der = np.array([ojo_der_x * w, ojo_der_y * h])
    
    dy = ojo_der[1] - ojo_izq[1]
    dx = ojo_der[0] - ojo_izq[0]
    angulo = np.degrees(np.arctan2(dy, dx))
    
    centro = ((ojo_izq[0] + ojo_der[0]) / 2, (ojo_izq[1] + ojo_der[1]) / 2)
    centro = (int(centro[0]), int(centro[1]))
    
    matriz_rot = cv2.getRotationMatrix2D(centro, angulo, 1.0)
    resultado = cv2.warpAffine(imagen, matriz_rot, (w, h))
    
    return resultado

def detectar_pose(landmarks, w, h):
    """
    Detecta la pose de la cabeza basado en puntos faciales
    """
    if landmarks is None:
        return None
    
    nariz = landmarks.landmark[INDICE_NARIZ]
    frente = landmarks.landmark[INDICE_FRENTE]
    barbilla = landmarks.landmark[INDICE_BARBILLA]
    mejilla_izq = landmarks.landmark[INDICE_MEJILLA_IZQ]
    mejilla_der = landmarks.landmark[INDICE_MEJILLA_DER]
    
    ancho_cara = abs(mejilla_der.x - mejilla_izq.x)
    alto_cara = abs(barbilla.y - frente.y)
    
    if nariz.x < mejilla_izq.x + ancho_cara * 0.3:
        return "izquierda"
    elif nariz.x > mejilla_der.x - ancho_cara * 0.3:
        return "derecha"
    
    if nariz.y < frente.y + alto_cara * 0.3:
        return "arriba"
    elif nariz.y > barbilla.y - alto_cara * 0.3:
        return "abajo"
    
    return "centro"

def registrar_persona():
    """
    Funcion principal para registrar una nueva persona
    Guarda FOTO + PUNTOS DE LA MALLA
    """
    print("="*60)
    print("REGISTRO HIBRIDO - GUARDA FOTO + PUNTOS DE LA MALLA")
    print("="*60)
    
    nombre = input("Ingresa el nombre de la persona: ").strip().lower()
    if not nombre:
        print("Nombre invalido")
        return
    
    # Crear carpetas para foto y puntos
    carpeta_fotos = os.path.join(RUTA_BASE_DATASET, nombre)
    carpeta_puntos = os.path.join(RUTA_PUNTOS_DATASET, nombre)
    os.makedirs(carpeta_fotos, exist_ok=True)
    os.makedirs(carpeta_puntos, exist_ok=True)
    
    print(f"Fotos se guardaran en: {carpeta_fotos}")
    print(f"Puntos se guardaran en: {carpeta_puntos}")
    print("\nINSTRUCCIONES:")
    print("  - Manten buena iluminacion")
    print("  - Primero debes parpadear para activar el sistema")
    print("  - Sigue las indicaciones en pantalla")
    print("  - Se guardara FOTO + PUNTOS 3D de cada pose")
    print("\nIniciando camara en 3 segundos...")
    time.sleep(3)
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("No se pudo abrir la camara")
        return
    
    poses = ['centro', 'izquierda', 'derecha', 'arriba', 'abajo']
    pose_actual_idx = 0
    fotos_tomadas = {pose: 0 for pose in poses}
    
    parpadeos_detectados = 0
    ultimo_estado_parpadeo = "abierto"
    verificacion_completada = False
    
    ultima_captura = 0
    mensaje_estado = ""
    color_mensaje = (0, 255, 0)
    
    print("\nCamara lista. Presiona 'ESC' para salir")
    print("-"*60)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)
        
        pose_actual = None
        ear_promedio = 0
        frame_alineado = None
        vector_puntos = None
        landmarks = None
        
        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0]
            
            # EXTRACCION DE PUNTOS (esto es lo nuevo)
            vector_puntos = extraer_vector_puntos(landmarks)
            
            # Alinear rostro para la foto
            frame_alineado = alinear_rostro(frame, landmarks)
            
            # Calculo de EAR para parpadeos
            puntos_ojo_izq = []
            puntos_ojo_der = []
            
            for idx in INDICES_OJO_IZQUIERDO:
                px = int(landmarks.landmark[idx].x * w)
                py = int(landmarks.landmark[idx].y * h)
                puntos_ojo_izq.append([px, py])
                cv2.circle(frame, (px, py), 2, (0, 255, 255), -1)
            
            for idx in INDICES_OJO_DERECHO:
                px = int(landmarks.landmark[idx].x * w)
                py = int(landmarks.landmark[idx].y * h)
                puntos_ojo_der.append([px, py])
                cv2.circle(frame, (px, py), 2, (255, 255, 0), -1)
            
            ear_izq = calcular_ear(puntos_ojo_izq)
            ear_der = calcular_ear(puntos_ojo_der)
            ear_promedio = (ear_izq + ear_der) / 2.0
            
            if ear_promedio < UMBRAL_EAR:
                estado_actual = "cerrado"
            else:
                estado_actual = "abierto"
            
            if not verificacion_completada:
                if ultimo_estado_parpadeo == "abierto" and estado_actual == "cerrado":
                    pass
                elif ultimo_estado_parpadeo == "cerrado" and estado_actual == "abierto":
                    parpadeos_detectados += 1
                    print(f"Parpadeo detectado: {parpadeos_detectados}/{PARPADEOS_NECESARIOS}")
                
                ultimo_estado_parpadeo = estado_actual
                
                if parpadeos_detectados >= PARPADEOS_NECESARIOS:
                    verificacion_completada = True
                    print("Verificacion completada! Comenzando captura...")
                    time.sleep(1)
            
            if verificacion_completada:
                # Dibujar malla (solo visual)
                mp_drawing.draw_landmarks(
                    frame, landmarks,
                    mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp_drawing_styles
                    .get_default_face_mesh_tesselation_style()
                )
                
                mp_drawing.draw_landmarks(
                    frame, landmarks,
                    mp_face_mesh.FACEMESH_CONTOURS,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp_drawing_styles
                    .get_default_face_mesh_contours_style()
                )
                
                pose_actual = detectar_pose(landmarks, w, h)
        
        # =============================================
        # GUARDAR FOTO + PUNTOS (cuando la pose es correcta)
        # =============================================
        if verificacion_completada and pose_actual_idx < len(poses) and frame_alineado is not None and vector_puntos is not None:
            tiempo_actual = time.time()
            if tiempo_actual - ultima_captura > PAUSA_ENTRE_FOTOS:
                
                pose_deseada = poses[pose_actual_idx]
                
                if pose_actual == pose_deseada:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                    
                    # 1. GUARDAR FOTO ALINEADA
                    nombre_foto = f"{pose_deseada}_{timestamp}.jpg"
                    ruta_foto = os.path.join(carpeta_fotos, nombre_foto)
                    cv2.imwrite(ruta_foto, frame_alineado)
                    
                    # 2. GUARDAR PUNTOS DE LA MALLA
                    nombre_puntos = f"{pose_deseada}_{timestamp}.pkl"
                    ruta_puntos = os.path.join(carpeta_puntos, nombre_puntos)
                    with open(ruta_puntos, 'wb') as f:
                        pickle.dump({
                            'vector': vector_puntos,
                            'pose': pose_deseada,
                            'timestamp': timestamp
                        }, f)
                    
                    fotos_tomadas[pose_deseada] += 1
                    ultima_captura = tiempo_actual
                    
                    mensaje_estado = f"Foto {fotos_tomadas[pose_deseada]}/{NUM_FOTOS_POR_POSICION}"
                    color_mensaje = (0, 255, 0)
                    
                    print(f"Guardado: {nombre_foto} + puntos")
                    
                    if fotos_tomadas[pose_deseada] >= NUM_FOTOS_POR_POSICION:
                        pose_actual_idx += 1
                        if pose_actual_idx >= len(poses):
                            print(f"\nRegistro completado para {nombre}")
                            print(f"Total: {sum(fotos_tomadas.values())} fotos + puntos")
                            break
                else:
                    mensaje_estado = f"Gira a la {pose_deseada}"
                    color_mensaje = (0, 165, 255)
        
        # Mostrar informacion en pantalla
        cv2.putText(frame, f"EAR: {ear_promedio:.2f}", (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        if not verificacion_completada:
            cv2.putText(frame, f"PARPADEA: {parpadeos_detectados}/{PARPADEOS_NECESARIOS}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
            cv2.putText(frame, "Mira a la camara", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        else:
            if pose_actual_idx < len(poses):
                pose_deseada = poses[pose_actual_idx]
                progreso = fotos_tomadas[pose_deseada]
                
                textos_pose = {
                    'centro': "MIRA AL FRENTE",
                    'izquierda': "GIRA IZQUIERDA",
                    'derecha': "GIRA DERECHA",
                    'arriba': "MIRA ARRIBA",
                    'abajo': "MIRA ABAJO"
                }
                
                overlay = frame.copy()
                cv2.rectangle(overlay, (0, 0), (w, 100), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
                
                cv2.putText(frame, textos_pose[pose_deseada], (50, 40),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.putText(frame, f"Progreso: {progreso}/{NUM_FOTOS_POR_POSICION}", (50, 80),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                cv2.putText(frame, mensaje_estado, (50, h-50),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.9, color_mensaje, 2)
        
        cv2.imshow("Registro Hibrido - PicMe", frame)
        
        if cv2.waitKey(1) & 0xFF == 27:  
            break
    
    cap.release()
    cv2.destroyAllWindows()
    face_mesh.close()
    
    print("\n" + "="*60)
    print("RESUMEN REGISTRO HIBRIDO")
    print("="*60)
    for pose, count in fotos_tomadas.items():
        print(f"  {pose}: {count} fotos + {count} archivos de puntos")
    print(f"Fotos en: {carpeta_fotos}")
    print(f"Puntos en: {carpeta_puntos}")
    print("="*60)

if __name__ == "__main__":
    registrar_persona()