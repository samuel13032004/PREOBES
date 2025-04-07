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
    X_analysis = X.copy()

    if 'IMC' in X_analysis.columns:
        X_analysis = X_analysis.drop('IMC', axis=1)

    X_analysis = X_analysis.drop(columns=['Weight'], axis=1)
    original_columns = X_analysis.columns.tolist()

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_analysis)

    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)

    feature_importances = model.feature_importances_

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

    # Normalizar importancias para que sumen 1 y ordenarlas
    feature_importance_df["Importancia"] /= feature_importance_df["Importancia"].sum()
    feature_importance_df = feature_importance_df.sort_values("Importancia", ascending=False)

    # Clasificar variables como modificables o no modificables
    no_modificables = ['Gender', 'Age', 'Height', 'family_history_with_overweight']
    modificables = [col for col in feature_importance_df.index if col not in no_modificables]

    # Filtrar solo las variables modificables y no modificables que están presentes en el índice
    df_modificables = feature_importance_df.loc[
        [col for col in modificables if col in feature_importance_df.index]
    ]

    df_no_modificables = feature_importance_df.loc[
        [col for col in no_modificables if col in feature_importance_df.index]
    ]

    df_modificables_normalizado = df_modificables.copy()
    # **Normalizar solo las importancias de las variables modificables** para que sumen exactamente 1
    df_modificables_normalizado["Importancia"] /= df_modificables_normalizado["Importancia"].sum()

    # Mostrar importancia de las variables modificables
    print("\n=== FACTORES QUE EL USUARIO PUEDE CONTROLAR ===")
    print("Importancia de factores modificables (ordenados por importancia):")
    print(df_modificables_normalizado)
    print("\n")
    print("Importancia de factores modificables sobre el total de factores (ordenados por importancia):")
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
    sns.barplot(x=df_modificables_normalizado.Importancia, y=df_modificables_normalizado.index, palette="viridis",
                hue=df_modificables_normalizado.index, legend=False, data=df_modificables_normalizado)
    plt.xlabel("Importancia Normalizada")
    plt.ylabel("Factores Controlables")
    plt.title("Importancia de los Factores de Riesgo Controlables para la Obesidad")
    plt.tight_layout()
    plt.savefig('graficos/factores_controlables.png')
    plt.show()
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
    plt.savefig('graficos/comparacion_factores.png')
    plt.show()
    plt.close()

    return {
        'factores_modificables': df_modificables,
        'factores_no_modificables': df_no_modificables,
        'modelo': model,
        'scaler': scaler
    }


def analizar_peso_por_edad(df):
    """
    Divide las edades en grupos, calcula la distribución de tipos de peso (NObeyesdad)
    y genera un gráfico de barras horizontales comparando los grupos de edad.

    Args:
        df (DataFrame): Dataset con columnas 'Age' y 'NObeyesdad'
    """

    # Verificar que estén las columnas necesarias
    if 'Age' not in df.columns or 'NObeyesdad' not in df.columns:
        print("Error: el DataFrame debe contener las columnas 'Age' y 'NObeyesdad'.")
        return

    # 1. Crear grupos de edad
    bins = [14, 20, 30, 40, 50, 61]
    labels = ['14-20', '21-30', '31-40', '41-50', '51-61']
    df['Grupo_Edad'] = pd.cut(df['Age'], bins=bins, labels=labels, include_lowest=True)

    # 2. Calcular proporciones por grupo de edad
    distribucion = df.groupby(['Grupo_Edad', 'NObeyesdad']).size().unstack().fillna(0)
    proporciones = distribucion.div(distribucion.sum(axis=1), axis=0)

    # 3. Mostrar valores
    print("\n📊 Cantidad de usuarios por grupo de edad y tipo de peso:")
    print(distribucion)

    print("\n📈 Proporciones por grupo de edad (0 a 1):")
    print(proporciones)

    # 3. Gráfico de barras horizontales
    proporciones.plot(kind='barh', stacked=True, figsize=(10, 6), colormap='tab20')
    plt.title('Distribución de Tipos de Peso por Grupo de Edad')
    plt.xlabel('Proporción')
    plt.ylabel('Grupo de Edad')
    plt.legend(title='Tipo de Peso', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.grid(axis='x', linestyle='--', alpha=0.6)
    plt.savefig('graficos/analisis_pesos_sectores_edad.png')
    plt.show()
    plt.close()