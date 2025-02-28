import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split


def analizar_importancia(X, y):
    """
    Analiza la importancia de las variables en el modelo Random Forest.

    Args:
        X: DataFrame con las variables predictoras
        y: Serie con la variable objetivo
    """
    # Estandarización de los datos
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Dividir los datos en conjunto de entrenamiento y prueba
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

    # Modelo de Random Forest para análisis de importancia
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Cálculo de importancias
    X_features = list(X.columns)

    feature_importances = model.feature_importances_
    feature_importance_df = pd.DataFrame(feature_importances, index=X.columns, columns=["Importancia"])

    # Normalizar importancias para que sumen 1
    feature_importance_df["Importancia"] /= feature_importance_df["Importancia"].sum()

    # Ordenar importancias
    feature_importance_df = feature_importance_df.sort_values("Importancia", ascending=False)

    # Mostrar importancia de las variables
    print("Importancia de las variables (normalizadas para sumar 1):")
    print(feature_importance_df)

    # Gráfico de barras con leyenda
    plt.figure(figsize=(10, 6))
    sns.barplot(x=feature_importance_df.Importancia, y=feature_importance_df.index, palette="viridis")
    plt.xlabel("Importancia Normalizada")
    plt.ylabel("Características")
    plt.title("Importancia de las Características en el Modelo")
    plt.show()

    return feature_importance_df