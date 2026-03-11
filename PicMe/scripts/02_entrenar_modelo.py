import cv2
import os
import numpy as np
import pickle
from sklearn.svm import SVC, OneClassSVM
from sklearn.ensemble import RandomForestClassifier
import joblib

#ok aqui algo importante, si bien las imagenes se guardan, lo que realmente permite la identifiacion, seria los puntos, y escalares
RUTA_DATASET = "C:/Users/jvier/OneDrive - UNIVERSIDAD DE CUNDINAMARCA/EVELIN YIJAN VIRGUEZ PARRA's files - PicMe/Códigos/2026-1/dataset"
RUTA_PUNTOS_DATASET = "C:/Users/jvier/OneDrive - UNIVERSIDAD DE CUNDINAMARCA/EVELIN YIJAN VIRGUEZ PARRA's files - PicMe/Códigos/2026-1/puntos_dataset"  #este es el importante
RUTA_MODELO_LBPH = "C:/Users/jvier/OneDrive - UNIVERSIDAD DE CUNDINAMARCA/EVELIN YIJAN VIRGUEZ PARRA's files - PicMe/Códigos/2026-1/modelos/modeloLBPH.xml"
RUTA_MODELO_PUNTOS = "C:/Users/jvier/OneDrive - UNIVERSIDAD DE CUNDINAMARCA/EVELIN YIJAN VIRGUEZ PARRA's files - PicMe/Códigos/2026-1/modelos/modelo_puntos.pkl"  #junto con este
RUTA_LABELS = "C:/Users/jvier/OneDrive - UNIVERSIDAD DE CUNDINAMARCA/EVELIN YIJAN VIRGUEZ PARRA's files - PicMe/Códigos/2026-1/modelos/labels.pkl"
RUTA_SCALER = "C:/Users/jvier/OneDrive - UNIVERSIDAD DE CUNDINAMARCA/EVELIN YIJAN VIRGUEZ PARRA's files - PicMe/Códigos/2026-1/modelos/scaler.pkl"  #y aca el escalador
RUTA_CENTROIDES = "C:/Users/jvier/OneDrive - UNIVERSIDAD DE CUNDINAMARCA/EVELIN YIJAN VIRGUEZ PARRA's files - PicMe/Códigos/2026-1/modelos/centroides.pkl"  #nuevo: para guardar centroides
RUTA_MODELOS_OCSVM = "C:/Users/jvier/OneDrive - UNIVERSIDAD DE CUNDINAMARCA/EVELIN YIJAN VIRGUEZ PARRA's files - PicMe/Códigos/2026-1/modelos/ocsvm/"  #carpeta para modelos one-class

#crear carpeta para modelos one-class
os.makedirs(RUTA_MODELOS_OCSVM, exist_ok=True)

TAMANO_IMAGEN = (200, 200)  # estas son buenas dimensiones para el modelo

def preparar_imagen(imagen_path):
    """
    Carga una imagen, la convierte a grises, redimensiona y ecualiza
    """
    img = cv2.imread(imagen_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None
    
    # redimensionar
    img = cv2.resize(img, TAMANO_IMAGEN)
    
    # aca mejora el contraste
    img = cv2.equalizeHist(img)
    
    return img

def cargar_puntos(puntos_path):
    """
    Carga un archivo de puntos .pkl y devuelve el vector de caracteristicas
    """
    with open(puntos_path, 'rb') as f:
        data = pickle.load(f)
    return data['vector']  # el vector es de 1404 dimensiones 468 puntos y las tres cordenadas, como bien dice evelin "z" es profundidad jajsajs, la adoro

def entrenar_modelo_hibrido():
    """
    Entrena TRES sistemas:
    1. LBPH con las FOTOS (textura) - opcional
    2. RandomForest con los PUNTOS 3D (geometria) - clasificacion
    3. One-Class SVM por persona - deteccion de desconocidos
    """
    print("="*60)
    print("ENTRENAMIENTO HIBRIDO - LBPH + PUNTOS 3D + ONE-CLASS SVM")
    print("="*60)
    
    # aca se verifica que la ruta si exista
    if not os.path.exists(RUTA_DATASET):
        print(f"ERROR: No existe la carpeta {RUTA_DATASET}")
        return
    
    if not os.path.exists(RUTA_PUNTOS_DATASET):
        print(f"ERROR: No existe la carpeta {RUTA_PUNTOS_DATASET}")
        print("Ejecuta primero 01_registro_hibrido.py")
        return
    
    # aca se obtiene la lista de personas, osea las carpetas
    personas = [p for p in os.listdir(RUTA_DATASET) 
                if os.path.isdir(os.path.join(RUTA_DATASET, p))]
    
    if len(personas) == 0:
        print("No se encontraron carpetas de personas en dataset/")
        return
    
    print(f"Personas detectadas: {personas}")
    print("-"*60)
    
    #datos de imagen para el modelo
    faces_lbph = []
    labels_lbph = []
    
    # Datos gemetricos
    puntos_geometria = []
    labels_geometria = []
    
    label_map = {}  # label_id seria el nombre de persona
    label_id = 0
    
    # Diccionario para almacenar puntos por persona (para one-class)
    puntos_por_persona = {}
    
    # recorrer cada persona
    for persona in personas:
        carpeta_fotos = os.path.join(RUTA_DATASET, persona)
        carpeta_puntos = os.path.join(RUTA_PUNTOS_DATASET, persona)
        
        # Verificar que existe la carpeta de puntos para esa persona en especifico
        if not os.path.exists(carpeta_puntos):
            print(f"  No hay carpeta de puntos para {persona}, se omiten sus puntos")
        
        print(f"\nProcesando: {persona}")
        
        #procesar las caputras
        archivos_fotos = os.listdir(carpeta_fotos)
        fotos_validas = 0
        
        for archivo in archivos_fotos:
            if not archivo.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
                
            ruta_foto = os.path.join(carpeta_fotos, archivo)
            img_procesada = preparar_imagen(ruta_foto)
            
            if img_procesada is not None:
                faces_lbph.append(img_procesada)
                labels_lbph.append(label_id)
                fotos_validas += 1
                
                if fotos_validas % 10 == 0:
                    print(f"  Fotos: {fotos_validas} cargadas...")
        
        print(f"  Fotos validas: {fotos_validas}")
        
        #procesar los puntos, lo importante
        if os.path.exists(carpeta_puntos):
            archivos_puntos = os.listdir(carpeta_puntos)
            puntos_validos = 0
            puntos_persona = []  # para one-class
            
            for archivo in archivos_puntos:
                if not archivo.endswith('.pkl'):
                    continue
                    
                ruta_punto = os.path.join(carpeta_puntos, archivo) 
                try:
                    vector_puntos = cargar_puntos(ruta_punto)
                    puntos_geometria.append(vector_puntos)
                    labels_geometria.append(label_id)
                    puntos_persona.append(vector_puntos)  # guardar para one-class
                    puntos_validos += 1
                    
                    if puntos_validos % 10 == 0:
                        print(f"  Puntos: {puntos_validos} cargados...")
                except Exception as e:
                    print(f"  Error cargando {archivo}: {e}")
            
            print(f"  Puntos validos: {puntos_validos}")
            if puntos_validos > 0:
                puntos_por_persona[persona] = np.array(puntos_persona)
        else:
            print(f"  No hay puntos para {persona}")
        
        if fotos_validas > 0 or puntos_validos > 0:
            label_map[label_id] = persona
            label_id += 1
        
        print(f"  Total para {persona}: {fotos_validas} fotos, {puntos_validos if 'puntos_validos' in locals() else 0} puntos")
    
    print("-"*60)
    
    #verificar que si haya datos para empezar jajsa
    if len(faces_lbph) == 0:
        print("ERROR: No hay fotos para entrenar LBPH")
        return
    
    if len(puntos_geometria) == 0:
        print("ERROR: No hay puntos para entrenar modelo geometrico")
        return
    
    print(f"\nRESUMEN GENERAL:")
    print(f"  Personas: {len(label_map)}")
    print(f"  Fotos para LBPH: {len(faces_lbph)}")
    print(f"  Puntos para modelo geometrico: {len(puntos_geometria)}")
    
    #aca empieza el entrenamiento con las fotos, depende mucho la calidad de la camara, con la de mi pc, vale verga porq texutra es lo que menos hay
    print("\n" + "="*60)
    print("ENTRENANDO LBPH (TEXTURA FACIAL)")
    print("="*60)
    
    os.makedirs(os.path.dirname(RUTA_MODELO_LBPH), exist_ok=True)
    
    recognizer = cv2.face.LBPHFaceRecognizer_create(
        radius=1,
        neighbors=8,
        grid_x=8,
        grid_y=8,
        threshold=80.0
    )
    
    recognizer.train(faces_lbph, np.array(labels_lbph))
    recognizer.write(RUTA_MODELO_LBPH)
    print(f"Modelo LBPH guardado en: {RUTA_MODELO_LBPH}")
    
    # =============================================
    # ENTRENAMIENTO CON PUNTOS (RANDOM FOREST)
    # =============================================
    print("\n" + "="*60)
    print("ENTRENANDO MODELO GEOMETRICO (PUNTOS 3D - RANDOM FOREST)")
    print("="*60)
    
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    
    X = np.array(puntos_geometria)
    y = np.array(labels_geometria)
    
    print(f"  Dimensiones de X: {X.shape}")  
    
    scaler = StandardScaler()
    X_normalizado = scaler.fit_transform(X)
    
    # aca entra lo bueno, el random forest para que cuando haya mas de una persona dentro del modelo, esta apartir de los puntos haga su arbol que identifique los puntos y asi haga la comparativa
    print("  Entrenando Random Forest...")
    clasificador_puntos = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42
    )
    
    # Dividir en entrenamiento y prueba para verificar
    X_train, X_test, y_train, y_test = train_test_split(
        X_normalizado, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Entrenar
    clasificador_puntos.fit(X_train, y_train)
    
    # Evaluar
    precision_train = clasificador_puntos.score(X_train, y_train)
    precision_test = clasificador_puntos.score(X_test, y_test)
    
    print(f"  Precision en entrenamiento: {precision_train*100:.2f}%")
    print(f"  Precision en prueba: {precision_test*100:.2f}%")
    
    # guardar modelo y scaler
    joblib.dump(clasificador_puntos, RUTA_MODELO_PUNTOS)
    joblib.dump(scaler, RUTA_SCALER)
    
    print(f"Modelo de puntos guardado en: {RUTA_MODELO_PUNTOS}")
    print(f"Scaler guardado en: {RUTA_SCALER}")
    
    # =============================================
    # ENTRENAMIENTO ONE-CLASS SVM POR PERSONA
    # =============================================
    print("\n" + "="*60)
    print("ENTRENANDO ONE-CLASS SVM POR PERSONA (DETECCION DE DESCONOCIDOS)")
    print("="*60)
    
    modelos_ocsvm = {}
    centroides = {}
    
    for persona, puntos_persona in puntos_por_persona.items():
        print(f"\n  Entrenando modelo para {persona}...")
        
        # Normalizar los puntos de esta persona con el mismo scaler
        X_persona = scaler.transform(puntos_persona)
        
        # Calcular centroide (para opcion de distancia)
        centroide = np.mean(X_persona, axis=0)
        centroides[persona] = centroide
        
        # Entrenar One-Class SVM
        # nu: proporcion esperada de outliers (0.1 = 10%)
        # gamma: que tan flexible es el limite
        ocsvm = OneClassSVM(
            nu=0.1,
            kernel='rbf',
            gamma='scale'
        )
        ocsvm.fit(X_persona)
        
        # Verificar que aprende bien
        train_pred = ocsvm.predict(X_persona)
        precision = np.mean(train_pred == 1) * 100
        print(f"     Precision en entrenamiento: {precision:.1f}%")
        print(f"     Muestras: {len(X_persona)}")
        
        # Guardar modelo
        ruta_modelo = os.path.join(RUTA_MODELOS_OCSVM, f"ocsvm_{persona}.pkl")
        joblib.dump(ocsvm, ruta_modelo)
        modelos_ocsvm[persona] = ocsvm
        print(f"     Modelo guardado: {ruta_modelo}")
    
    # Guardar centroides
    joblib.dump(centroides, RUTA_CENTROIDES)
    print(f"\n  Centroides guardados en: {RUTA_CENTROIDES}")
    print(f"  Total modelos One-Class SVM: {len(modelos_ocsvm)}")
   
    # Guardar labels
    with open(RUTA_LABELS, 'wb') as f:
        pickle.dump(label_map, f)
    print(f"Labels guardados en: {RUTA_LABELS}")
    
    print("\n" + "="*60)
    print("ENTRENAMIENTO HIBRIDO COMPLETADO")
    print("="*60)
    print("\nModelos generados:")
    print(f"  - LBPH (textura): {RUTA_MODELO_LBPH}")
    print(f"  - Random Forest (puntos 3D): {RUTA_MODELO_PUNTOS}")
    print(f"  - One-Class SVM (por persona): {RUTA_MODELOS_OCSVM}")
    print(f"  - Centroides: {RUTA_CENTROIDES}")
    print(f"  - Labels: {RUTA_LABELS}")
    print("="*60)

if __name__ == "__main__":
    entrenar_modelo_hibrido()