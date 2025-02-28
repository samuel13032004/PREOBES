import os
import datetime
from cargar_datos import cargar_datos
from analisis_importancia import analizar_importancia
from clasificacion import entrenar_modelo, predecir
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


def main():
    """
    Función principal que ejecuta todo el flujo de trabajo:
    1. Carga de datos desde MongoDB
    2. Análisis de importancia de variables
    3. Entrenamiento del modelo de clasificación
    4. Guardar resultados
    """
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
        importancias = analizar_importancia(X, y)
        print(f"✓ Análisis de importancia completado")

        # Guardar importancias

        # Guardar gráfico de importancias
        plt.figure(figsize=(10, 6))
        sns.barplot(x=importancias.Importancia, y=importancias.index, palette="viridis")
        plt.xlabel("Importancia Normalizada")
        plt.ylabel("Características")
        plt.title("Importancia de las Características en el Modelo")
        plt.tight_layout()
        plt.close()

    except Exception as e:
        print(f"✗ Error en análisis de importancia: {str(e)}")

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


if __name__ == "__main__":
    main()


