import pymongo
import pandas as pd
from sklearn.preprocessing import LabelEncoder

# Establecer opción para mostrar todas las columnas
pd.set_option('display.max_columns', None)

def cargar_datos():
    """
    Conecta a MongoDB y carga los datos de obesidad en un DataFrame.

    Returns:
        tuple: (DataFrame con los datos, variable objetivo)
    """
    # Conectar a MongoDB
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["ObesityDataSet"]
    collection = db["ObesityDataSet"]

    # Extraer los datos de la colección
    data = list(collection.find())
    df = pd.DataFrame(data)

    # Eliminar la columna '_id' si existe
    if "_id" in df.columns:
        df = df.drop(columns=["_id"])
    df['IMC'] = df['Weight'] / (df['Height'] ** 2)

    # Visualizar información básica del dataset
    print("Primeras filas del dataset:")
    print(df.head())

    print("\nValores únicos para variables categóricas:")
    for col in df.select_dtypes(include=['object']).columns:
        print(f"{col}: {df[col].unique()}")

    # Convertir variables categóricas en variables numéricas
    categorical_columns = ['Gender', 'family_history_with_overweight', 'FAVC', 'CAEC',
                           'SMOKE', 'SCC', 'CALC', 'MTRANS']

    for col in categorical_columns:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col])

    # Separar las características (X) y la variable objetivo (y)
    X = df.drop(columns=["NObeyesdad"])
    y = df["NObeyesdad"]

    return df, X, y
