from flask import Flask
import os
import pymongo
import pandas as pd
from neo4j import GraphDatabase
from cargar_datos.cargar_datos_mongodb import cargar_datos_mongo, cargar_datos
from rutas_backend.rutas import configurar_rutas_configuracion
from utilidades.modelos import cargar_modelos
from analisis_variables.analisis_importancia_clasificacion import analizar_importancia
from correlaciones.analisis_relaciones import analisis_completo_neo4j, crear_matriz_correlacion
from entrenamiento_modelo.clasificacion import entrenar_modelo, predecir
from analisis_variables.analisis_factores import analizar_factores_obesidad, analizar_peso_por_edad

CONFIG_FILE = '.analysis_config'


def guardar_decision(decision):
    """Guarda la última decisión tomada."""
    with open(CONFIG_FILE, 'w') as f:
        f.write(decision)


def obtener_ultima_decision():
    """Obtiene la última decisión guardada."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return f.read().strip()
    return None


def realizar_analisis():
    """
    Función que ejecuta el análisis de datos de obesidad
    """
    print("=" * 80)
    print("ANÁLISIS DE DATASET DE OBESIDAD")
    print("=" * 80)
    print("\n1. CARGANDO DATOS DESDE MONGODB...")
    try:
        df, X, y = cargar_datos()
        print(f"Datos cargados exitosamente: {len(df)} registros, {len(X.columns)} variables")
    except Exception as e:
        print(f"X Error al cargar datos: {str(e)}")
        return None, None, None, None
    print("\n2. ANALIZANDO IMPORTANCIA DE VARIABLES...")
    try:
        analizar_importancia(X, y)
    except Exception as e:
        print(f"X Error en análisis de importancia: {str(e)}")

    """
        print("\n3. ENTRENANDO MODELO DE CLASIFICACIÓN...")
        try:
            modelo, le, scaler = entrenar_modelo(X, y)
            print(f"Modelo entrenado exitosamente")

            muestra = X.iloc[:5]
            predicciones = predecir(modelo, le, scaler, muestra)

            resultados = pd.DataFrame({
                'Predicción': predicciones,
                'Valor real': y.iloc[:5].values
            })

            print("\nEjemplo de predicciones:")
            print(resultados)

        except Exception as e:
            print(f"X Error en entrenamiento del modelo: {str(e)}")

        print("\n" + "=" * 80)
        print("=" * 80)
    """

    print("\n4. ANALIZANDO FACTORES DE OBESIDAD...")
    try:
        analizar_peso_por_edad(df)
        resultados_analisis = analizar_factores_obesidad(X, y)
        print(f"Análisis de factores de obesidad completado")
        factores_modificables = resultados_analisis['factores_modificables']
        factores_no_modificables = resultados_analisis['factores_no_modificables']
        modelo_rf = resultados_analisis['modelo']
        scaler_rf = resultados_analisis['scaler']
        print("\nFactores modificables más importantes:")
        print(factores_modificables.head())
        print("\nFactores no modificables más importantes:")
        print(factores_no_modificables.head())
        le = None
        model_columns = X.columns.tolist()
        print("\n" + "=" * 80)
        print("ANÁLISIS COMPLETADO")
        print("=" * 80)

        print("5. Iniciando análisis de relaciones entre variables...")
        URI = "bolt://localhost:7687"
        USER = "neo4j"
        PASSWORD = "ObesityDataSet"
        driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
        analisis_completo_neo4j()
        crear_matriz_correlacion()
        driver.close()
        return modelo_rf, scaler_rf, le, model_columns
    except Exception as e:
        print(f"X Error en análisis de factores de obesidad: {str(e)}")
        return None, None, None, None


modelo = None
scaler = None
le = None
model_columns = None
users_collection = None
reports_collection = None


def inicializar_modelos():
    global modelo, scaler, le, model_columns

    if os.environ.get("FLASK_RUN_FROM_CLI") != "false":
        obtener_ultima_decision()

        ejecutar_analisis = input("¿Desea ejecutar el análisis de datos? (s/n): ").lower()

        guardar_decision(ejecutar_analisis)

        if ejecutar_analisis == 's':
            print("Iniciando análisis de datos...")
            modelo, scaler, le, model_columns = realizar_analisis()
            guardar_decision("n")

        else:
            try:
                modelo, scaler, le, model_columns = cargar_modelos()
                print("Modelos cargados exitosamente desde archivos existentes")
            except Exception as e:
                print(f"X Error: No se pueden cargar los modelos. Debe ejecutar el análisis primero: {str(e)}")
                exit(1)
    else:
        guardar_decision("n")
        ultima_decision = obtener_ultima_decision()
        if ultima_decision == 's':
            try:
                modelo, scaler, le, model_columns = realizar_analisis()
            except Exception as e:
                print(f"X Error en el análisis: {str(e)}")
                exit(1)
        else:
            try:
                modelo, scaler, le, model_columns = cargar_modelos()
            except Exception as e:
                print(f"X Error al cargar modelos: {str(e)}")
                exit(1)

    return modelo, scaler, le, model_columns


app = Flask(__name__)
app.config['DEBUG'] = True
app.secret_key = 'PREOBES'

modelo, scaler, le, model_columns = inicializar_modelos()

if __name__ == '__main__':
    os.environ["FLASK_RUN_FROM_CLI"] = "true"

    token_openai = os.getenv("apikey")
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db, db_collection, users_collection, reports_collection = cargar_datos_mongo(client)
    configurar_rutas_configuracion(app, modelo, scaler, le, model_columns, db_collection,
                                   users_collection, reports_collection)

    print("Iniciando servidor Flask...")

    os.environ["FLASK_RUN_FROM_CLI"] = "false"

    app.run(host='localhost', port=8080, debug=True, use_reloader=True)
