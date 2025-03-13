import os
import datetime

from neo4j import GraphDatabase
from tensorboard import summary

from cargar_datos.cargar_datos_mongodb import cargar_datos
from analisis_variables.analisis_importancia_clasificacion import analizar_importancia
from correlaciones.analisis_relaciones import analisis_completo_neo4j
from entrenamiento_modelo.clasificacion import entrenar_modelo, predecir
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from analisis_variables.analisis_factores import analizar_factores_obesidad

def main():

    print("=" * 80)
    print("ANÁLISIS DE DATASET DE OBESIDAD")
    print("=" * 80)

    # 1. Cargar datos
    print("\n1. CARGANDO DATOS DESDE MONGODB...")
    try:
        df, X, y = cargar_datos()
        print(f"✓ Datos cargados exitosamente: {len(df)} registros, {len(X.columns)} variables")

    except Exception as e:
        print(f"✗ Error al cargar datos: {str(e)}")
        return

    # 2. Análisis de importancia
    print("\n2. ANALIZANDO IMPORTANCIA DE VARIABLES...")
    try:
        analizar_importancia(X, y)
    except Exception as e:
        print(f"✗ Error en análisis de importancia: {str(e)}")

    """
    # 3. Entrenamiento del modelo
    print("\n3. ENTRENANDO MODELO DE CLASIFICACIÓN...")
    try:
        modelo, le, scaler = entrenar_modelo(X, y)
        print(f"✓ Modelo entrenado exitosamente")

        # Hacer algunas predicciones de ejemplo (usando los primeros 5 registros)
        muestra = X.iloc[:5]
        predicciones = predecir(modelo, le, scaler, muestra)

        # Guardar resultados de ejemplo
        resultados = pd.DataFrame({
            'Predicción': predicciones,
            'Valor real': y.iloc[:5].values
        })

        print("\nEjemplo de predicciones:")
        print(resultados)

    except Exception as e:
        print(f"✗ Error en entrenamiento del modelo: {str(e)}")

    print("\n" + "=" * 80)
    print("=" * 80)
    """


    # 4. Análisis de factores de obesidad
    print("\n4. ANALIZANDO FACTORES DE OBESIDAD...")

    try:
        resultados_analisis = analizar_factores_obesidad(X, y)
        print(f"✓ Análisis de factores de obesidad completado")

        # Extraer componentes del resultado
        factores_modificables = resultados_analisis['factores_modificables']
        factores_no_modificables = resultados_analisis['factores_no_modificables']
        modelo_rf = resultados_analisis['modelo']
        scaler_rf = resultados_analisis['scaler']


        print("\nFactores modificables más importantes:")
        print(factores_modificables.head())

        print("\nFactores no modificables más importantes:")
        print(factores_no_modificables.head())

    except Exception as e:
        print(f"✗ Error en análisis de factores de obesidad: {str(e)}")
        return

    print("\n" + "=" * 80)
    print("ANÁLISIS COMPLETADO")
    print("=" * 80)


    print("5. Iniciando análisis de relaciones entre variables...")

    URI = "bolt://localhost:7687"
    USER = "neo4j"
    PASSWORD = "ObesityDataSet"
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

    correlaciones = analisis_completo_neo4j()

    driver.close()

if __name__ == "__main__":
    main()
