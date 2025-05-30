import pandas as pd
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

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    X_features = list(X.columns)

    feature_importances = model.feature_importances_
    feature_importance_df = pd.DataFrame(feature_importances, index=X.columns, columns=["Importancia"])

    feature_importance_df["Importancia"] /= feature_importance_df["Importancia"].sum()
    feature_importance_df = feature_importance_df.sort_values("Importancia", ascending=False)

    print("Importancia de las variables (normalizadas para sumar 1):")
    print(feature_importance_df)

    plt.figure(figsize=(10, 6))
    sns.barplot(x="Importancia", y=feature_importance_df.index, hue=feature_importance_df.index, legend=False,
                palette="viridis", data=feature_importance_df)
    plt.xlabel("Importancia Normalizada")
    plt.ylabel("Características")
    plt.title("Importancia de las Características en el Modelo")
    plt.savefig("../PREOBES/graficos/importancia_caracteristicas.png")
    plt.show()

    return feature_importance_df
