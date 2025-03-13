import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score


def entrenar_modelo(X, y):
    """
    Entrena un modelo de clasificación Random Forest optimizado.

    Args:
        X: DataFrame con las variables predictoras
        y: Serie con la variable objetivo

    Returns:
        tuple: (modelo entrenado, encoder de etiquetas, scaler)
    """
    # Aplicar one-hot encoding a variables categóricas si es necesario
    X = pd.get_dummies(X, drop_first=True)

    # Codificar la variable objetivo a valores numéricos
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    # Dividir el dataset en entrenamiento y prueba
    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

    # Escalar las características numéricas
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Crear diccionario de pesos basado en las etiquetas
    pesos = {
        'Insufficient_Weight': 2.0,  # Aumentar si es clase minoritaria
        'Normal_Weight': 1.0,  # Reducir este peso
        'Obesity_Type_I': 2.0,
        'Obesity_Type_II': 2.5,
        'Obesity_Type_III': 3.0,  # Mayor peso para clases graves minoritarias
        'Overweight_Level_I': 2.0,
        'Overweight_Level_II': 2.0
    }
    pesos_numericos = {i: pesos[etiqueta] for i, etiqueta in enumerate(le.classes_)}

    # Configuración para GridSearchCV
    param_grid = {
        'n_estimators': [100, 200, 300],
        'max_depth': [None, 10, 20],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4],
        'max_features': ['sqrt', 'log2'],
        'bootstrap': [True, False]
    }

    # Entrenamiento con búsqueda de hiperparámetros
    print("Iniciando búsqueda de hiperparámetros óptimos...")
    rf = RandomForestClassifier(random_state=42, class_weight=pesos_numericos)
    grid = GridSearchCV(estimator=rf, param_grid=param_grid, cv=5, scoring='accuracy', n_jobs=-1)
    grid.fit(X_train_scaled, y_train)

    print("Mejores parámetros encontrados:", grid.best_params_)

    # Obtener el mejor modelo
    best_rf = grid.best_estimator_

    # Evaluar el modelo
    y_pred = best_rf.predict(X_test_scaled)
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=le.classes_)

    print("\nExactitud del modelo:", accuracy)
    print("\nReporte de clasificación:")
    print(report)

    # Guardar el modelo
    with open('resultados_modelo/modelo_obesidad.pkl', 'wb') as f:
        pickle.dump((best_rf, le, scaler), f)

    with open("resultados_modelo/scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)

    with open("resultados_modelo/label_encoder.pkl", "wb") as f:
        pickle.dump(le, f)

    with open("resultados_modelo/columns.pkl", "wb") as f:
        pickle.dump(X.columns.tolist(), f)

    print("Modelo guardado como 'modelo_obesidad.pkl'")

    return best_rf, le, scaler


def predecir(modelo, le, scaler, nuevos_datos):
    """
    Realiza predicciones con el modelo entrenado.

    Args:
        modelo: Modelo RandomForest entrenado
        le: LabelEncoder para transformar las etiquetas
        scaler: StandardScaler para escalar los datos
        nuevos_datos: DataFrame con nuevos datos para predecir

    Returns:
        array: Predicciones en formato legible
    """
    # Preparar los datos
    nuevos_datos = pd.get_dummies(nuevos_datos, drop_first=True)

    # Asegurar que tenemos las mismas columnas que en el entrenamiento
    # (Este código es simplificado, habría que manejar columnas faltantes o adicionales)

    # Escalar los datos
    nuevos_datos_scaled = scaler.transform(nuevos_datos)

    # Predecir
    pred_encoded = modelo.predict(nuevos_datos_scaled)

    # Convertir a etiquetas legibles
    predicciones = le.inverse_transform(pred_encoded)

    return predicciones
