import cv2
import mediapipe as mp
import numpy as np
import joblib
import pickle
import time
import os
from collections import deque


RUTA_SCALER = "C:/Users/jvier/OneDrive - UNIVERSIDAD DE CUNDINAMARCA/EVELIN YIJAN VIRGUEZ PARRA's files - PicMe/Códigos/2026-1/modelos/scaler.pkl"
RUTA_LABELS = "C:/Users/jvier/OneDrive - UNIVERSIDAD DE CUNDINAMARCA/EVELIN YIJAN VIRGUEZ PARRA's files - PicMe/Códigos/2026-1/PicMe/modelos/labels.pkl"
RUTA_MODELOS_OCSVM = "C:/Users/jvier/OneDrive - UNIVERSIDAD DE CUNDINAMARCA/EVELIN YIJAN VIRGUEZ PARRA's files - PicMe/Códigos/2026-1//modelos/ocsvm/"  
RUTA_CENTROIDES = "C:/Users/jvier/OneDrive - UNIVERSIDAD DE CUNDINAMARCA/EVELIN YIJAN VIRGUEZ PARRA's files - PicMe/Códigos/2026-1/modelos/centroides.pkl"  

scaler = joblib.load(RUTA_SCALER)
with open(RUTA_LABELS, 'rb') as f:
    label_map = pickle.load(f)

modelos_ocsvm = {}
print("Cargando modelos one-class SVM...")
for persona in label_map.values():
    ruta_modelo = os.path.join(RUTA_MODELOS_OCSVM, f"ocsvm_{persona}.pkl")
    if os.path.exists(ruta_modelo):
        modelos_ocsvm[persona] = joblib.load(ruta_modelo)
        print(f"  Modelo cargado: {persona}")

centroides = {}
if os.path.exists(RUTA_CENTROIDES):
    centroides = joblib.load(RUTA_CENTROIDES)
    print("Centroides cargados")

# incia mediapipe con la mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# indices de los ojos para la formula de evelin
INDICES_OJO_IZQUIERDO = [33, 160, 158, 133, 153, 144]
INDICES_OJO_DERECHO = [362, 385, 387, 263, 373, 380]

def calcular_ear(coordenadas_ojos):
    """
    Calcula el Eye Aspect Ratio (EAR)
    """
    try:
        a = np.linalg.norm(np.array(coordenadas_ojos[1]) - np.array(coordenadas_ojos[5]))
        b = np.linalg.norm(np.array(coordenadas_ojos[2]) - np.array(coordenadas_ojos[4]))
        c = np.linalg.norm(np.array(coordenadas_ojos[0]) - np.array(coordenadas_ojos[3]))
        ear = (a + b) / (2.0 * c)
        return ear
    except:
        return 0.0

def extraer_vector_puntos(landmarks, w, h):
    vector = []
    for punto in landmarks.landmark:
        vector.append(punto.x)
        vector.append(punto.y)
        vector.append(punto.z)
    return np.array(vector).reshape(1, -1)

UMBRAL_EAR = 0.22        
PARPADEOS_NECESARIOS = 3    
TIEMPO_VERIFICADO = 5       

ultimo_estado = "abierto"
parpadeos_contados = 0
verificado = False
ultimo_tiempo_verificado = 0
estado_mostrar = "NO VERIFICADO"

# captura de video
cap = cv2.VideoCapture(0)
print("Presiona 'q' para salir")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    frame = cv2.flip(frame, 1)
    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    results = face_mesh.process(rgb)
    
    if results.multi_face_landmarks:
        landmarks = results.multi_face_landmarks[0]
        
    
        # obtiene puntos de los ojos
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
        
        # Calculo de evelin
        ear_izq = calcular_ear(puntos_ojo_izq)
        ear_der = calcular_ear(puntos_ojo_der)
        ear = (ear_izq + ear_der) / 2.0
        
        # determinar si estado
        if ear < UMBRAL_EAR:
            estado_actual = "cerrado"
        else:
            estado_actual = "abierto"
        
        # Contar parpadeos solo al pasar determinado tiempo
        tiempo_actual = time.time()
        if tiempo_actual - ultimo_tiempo_verificado > TIEMPO_VERIFICADO:
            verificado = False
            
            if ultimo_estado == "abierto" and estado_actual == "cerrado":
                paso = "cerrando"
            elif ultimo_estado == "cerrado" and estado_actual == "abierto":
                parpadeos_contados += 1
                print(f"Parpadeo {parpadeos_contados}/{PARPADEOS_NECESARIOS}")
            
            ultimo_estado = estado_actual
            
            if parpadeos_contados >= PARPADEOS_NECESARIOS:
                verificado = True
                ultimo_tiempo_verificado = tiempo_actual
                parpadeos_contados = 0
                print("Persona verificada - acceso permitido")
        
        # preddicion estandar    
        if verificado:
            vector = extraer_vector_puntos(landmarks, w, h)
            vector_norm = scaler.transform(vector)
      
            persona_detectada = None
            puntaje_max = -float('inf')
            
            for persona, modelo in modelos_ocsvm.items():
                # si la preddicion es -1 no pertence
                prediccion = modelo.predict(vector_norm)[0]
                puntaje = modelo.decision_function(vector_norm)[0]
                
                if prediccion == 1 and puntaje > puntaje_max:
                    puntaje_max = puntaje
                    persona_detectada = persona
            
    
            if persona_detectada is None and centroides:
                dist_min = float('inf')
                for persona, centroide in centroides.items():
                    dist = np.linalg.norm(vector_norm - centroide)
                    if dist < dist_min:
                        dist_min = dist
                        if dist_min < 3.0:  # umbral de distancia
                            persona_detectada = persona
            
    
            if persona_detectada:
                estado_mostrar = f"{persona_detectada}"
                color_texto = (0, 255, 0)
                
                # Mostrar puntaje si existe
                if puntaje_max != -float('inf'):
                    estado_mostrar += f" ({puntaje_max:.2f})"
            else:
                estado_mostrar = "DESCONOCIDO"
                color_texto = (0, 0, 255)
        else:
            estado_mostrar = f"PARPADEA: {parpadeos_contados}/{PARPADEOS_NECESARIOS}"
            color_texto = (0, 165, 255)
        
        cv2.putText(frame, estado_mostrar, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_texto, 2)
        cv2.putText(frame, f"EAR: {ear:.2f}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Mostrar modo de deteccion
        modo_texto = "Modo: One-Class SVM" if modelos_ocsvm else "Modo: Distancia"
        cv2.putText(frame, modo_texto, (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # dibujar los puntos de la malla nomas pa verlos
        for punto in landmarks.landmark:
            x_px = int(punto.x * w)
            y_px = int(punto.y * h)
            cv2.circle(frame, (x_px, y_px), 1, (0, 255, 255), -1)
    
    cv2.imshow("One-Class SVM + Parpadeo", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
face_mesh.close()