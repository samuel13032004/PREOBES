import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split


def analizar_factores_obesidad(X, y):
    """
    Analiza la importancia de las variables en el modelo Random Forest, con enfoque
    en factores modificables que el usuario puede controlar para prevenir la obesidad.

    Args:
        X: DataFrame con las variables predictoras
        y: Serie con la variable objetivo
    """
    # Crear una copia del DataFrame para no modificar el original
    X_analysis = X.copy()

    # Eliminar IMC si existe en el DataFrame
    if 'IMC' in X_analysis.columns:
        X_analysis = X_analysis.drop('IMC', axis=1)

    # Guardar las columnas originales para usarlas más tarde
    original_columns = X_analysis.columns.tolist()

    # Estandarización de los datos
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_analysis)

    # Dividir los datos en conjunto de entrenamiento y prueba
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

    # Modelo de Random Forest para análisis de importancia
    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)

    # Cálculo de importancias - asegurarse de usar las columnas correctas
    feature_importances = model.feature_importances_

    # Verificar que la longitud de feature_importances coincida con el número de columnas
    if len(feature_importances) != len(original_columns):
        print(
            f"ADVERTENCIA: Discrepancia en dimensiones. Features: {len(feature_importances)}, Columnas: {len(original_columns)}")
        # Si hay discrepancia, usar solo las primeras n características
        feature_importance_df = pd.DataFrame(
            feature_importances,
            index=original_columns[:len(feature_importances)],
            columns=["Importancia"]
        )
    else:
        feature_importance_df = pd.DataFrame(
            feature_importances,
            index=original_columns,
            columns=["Importancia"]
        )

    # Normalizar importancias para que sumen 1
    feature_importance_df["Importancia"] /= feature_importance_df["Importancia"].sum()

    # Ordenar importancias
    feature_importance_df = feature_importance_df.sort_values("Importancia", ascending=False)

    # Clasificar variables como modificables o no modificables
    no_modificables = ['Gender', 'Age', 'Height', 'family_history_with_overweight', 'Weight']

    # Verificamos que 'Weight' esté en las columnas (lo movemos a modificables aunque parece confuso)
    if 'Weight' in feature_importance_df.index:
        modificables = [col for col in feature_importance_df.index if col not in no_modificables]
    else:
        modificables = [col for col in feature_importance_df.index if col not in no_modificables]
        print("ADVERTENCIA: 'Weight' no está en las columnas del modelo")

    # Filtrar solo las variables modificables y no modificables que están presentes en el índice
    df_modificables = feature_importance_df.loc[
        [col for col in modificables if col in feature_importance_df.index]
    ]

    df_no_modificables = feature_importance_df.loc[
        [col for col in no_modificables if col in feature_importance_df.index]
    ]

    # Mostrar importancia de las variables modificables
    print("\n=== FACTORES QUE EL USUARIO PUEDE CONTROLAR ===")
    print("Importancia de factores modificables (ordenados por importancia):")
    print(df_modificables)

    print("\n=== FACTORES NO CONTROLABLES ===")
    print(df_no_modificables)

    # Mostrar importancia total de cada grupo
    imp_modificables = df_modificables["Importancia"].sum()
    imp_no_modificables = df_no_modificables["Importancia"].sum()

    print(f"\nImportancia total de factores controlables: {imp_modificables * 100:.1f}%")
    print(f"Importancia total de factores no controlables: {imp_no_modificables * 100:.1f}%")

    # Gráfico de barras para variables modificables con leyenda
    plt.figure(figsize=(10, 6))
    sns.barplot(x=df_modificables.Importancia, y=df_modificables.index, palette="viridis")
    plt.xlabel("Importancia Normalizada")
    plt.ylabel("Factores Controlables")
    plt.title("Importancia de los Factores de Riesgo Controlables para la Obesidad")
    plt.tight_layout()
    plt.savefig('factores_controlables.png')
    plt.show()  # Luego la mostramos en pantalla
    plt.close()

    # Gráfico de pastel comparando modificables vs no modificables
    plt.figure(figsize=(8, 8))
    plt.pie([imp_modificables, imp_no_modificables],
            labels=['Factores Controlables', 'Factores No Controlables'],
            autopct='%1.1f%%',
            startangle=90,
            colors=['#2ecc71', '#3498db'])
    plt.title('Impacto Relativo de Factores Controlables vs. No Controlables')
    plt.tight_layout()
    plt.savefig('comparacion_factores.png')
    plt.show()  # Luego la mostramos en pantalla
    plt.close()

    """
    print("\n=== INTERPRETACIÓN DE FACTORES MODIFICABLES ===")
    for idx, (factor, importancia) in enumerate(df_modificables.head(5).items(), 1):
        print(f"{idx}. {factor}: {importancia * 100:.2f}%")
        if factor == 'Weight':
            print("   - El peso es un factor controlable a través de dieta y ejercicio")
        elif factor == 'FAVC':
            print("   - Reducir el consumo frecuente de alimentos altos en calorías tiene un impacto significativo")
        elif factor == 'FCVC':
            print("   - Aumentar el consumo de verduras puede ayudar a controlar el peso")
        elif factor == 'CH2O':
            print("   - Beber más agua ayuda a mantener la saciedad y apoya el metabolismo")
        elif factor == 'FAF':
            print("   - Incrementar la frecuencia de actividad física es clave para el control de peso")
        elif factor == 'TUE':
            print("   - Reducir el tiempo frente a pantallas puede disminuir el sedentarismo")
        elif factor == 'NCP':
            print("   - Mantener un número adecuado de comidas principales ayuda a regular el metabolismo")
        elif factor == 'CAEC':
            print("   - Controlar los alimentos entre comidas puede reducir la ingesta calórica total")
        elif factor == 'MTRANS':
            print("   - El modo de transporte activo (caminar, bicicleta) puede aumentar la actividad física diaria")
        elif factor == 'CALC':
            print("   - Reducir el consumo de alcohol puede disminuir la ingesta calórica innecesaria")
        elif factor == 'SCC':
            print("   - El control de calorías puede ayudar a mantener un balance energético adecuado")
        elif factor == 'SMOKE':
            print("   - Dejar de fumar puede mejorar la salud general y el metabolismo")

    # Recomendaciones basadas en los factores más importantes
    print("\n=== RECOMENDACIONES PRINCIPALES ===")
    print("Basado en los factores modificables más importantes, se recomienda:")
    for idx, factor in enumerate(list(df_modificables.head(3).index), 1):
        if factor == 'Weight':
            print(f"{idx}. Establecer metas realistas de pérdida de peso gradual (0.5-1kg por semana)")
        elif factor == 'FAVC':
            print(f"{idx}. Reducir el consumo de alimentos procesados y altos en calorías")
        elif factor == 'FCVC':
            print(f"{idx}. Aumentar el consumo de vegetales a 2-3 porciones por comida")
        elif factor == 'CH2O':
            print(f"{idx}. Incrementar el consumo de agua a 2L o más por día")
        elif factor == 'FAF':
            print(f"{idx}. Realizar actividad física al menos 3-5 veces por semana, 30 minutos por sesión")
        elif factor == 'TUE':
            print(f"{idx}. Limitar el tiempo de uso de dispositivos tecnológicos, tomando descansos activos")
    """

    return {
        'factores_modificables': df_modificables,
        'factores_no_modificables': df_no_modificables,
        'modelo': model,
        'scaler': scaler
    }
