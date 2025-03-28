import pymongo
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import MinMaxScaler

# Establecer opción para mostrar todas las columnas
pd.set_option('display.max_columns', None)

def cargar_datos():
    """
    Conecta a MongoDB y carga los datos de obesidad en un DataFrame.

    Returns:
        tuple: (DataFrame con los datos, variable objetivo)
    """
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["ObesityDataSet"]
    collection = db["ObesityDataSet"]

    # Extraer los datos de la colección
    data = list(collection.find())
    df = pd.DataFrame(data)

    if "_id" in df.columns:
        df = df.drop(columns=["_id"])

    df['IMC'] = df['Weight'] / (df['Height'] ** 2)

    #print("Primeras filas del dataset:")
    # print(df.head())

    #print("\nValores únicos para variables categóricas:")
    # for col in df.select_dtypes(include=['object']).columns:
    #  print(f"{col}: {df[col].unique()}")

    # Convertir variables categóricas en variables numéricas
    categorical_columns = ['Gender', 'family_history_with_overweight', 'FAVC', 'CAEC',
                           'SMOKE', 'SCC', 'CALC', 'MTRANS']

    for col in categorical_columns:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col])
        #print(df[col])

    # Separar las características (X) y la variable objetivo (y)
    X = df.drop(columns=["NObeyesdad"])
    y = df["NObeyesdad"]

    return df, X, y


def obtener_valores_extremos(df):
    """
    Obtiene los valores máximos y mínimos de todas las columnas numéricas.

    Args:
        df: DataFrame con los datos

    Returns:
        DataFrame con los valores máximos y mínimos
    """
    # Seleccionar solo las columnas numéricas
    numeric_df = df.select_dtypes(include=['number'])

    # Calcular valores máximos y mínimos
    max_values = numeric_df.max()
    min_values = numeric_df.min()

    # Crear un DataFrame con los resultados
    result_df = pd.DataFrame({
        'Valor_Mínimo': min_values,
        'Valor_Máximo': max_values
    })

    return result_df

df, X, y = cargar_datos()

# Obtener y mostrar los valores máximos y mínimos
valores_extremos = obtener_valores_extremos(df)
#print("\nValores máximos y mínimos de columnas numéricas:")
#print(valores_extremos)


def cargar_datos_mongo(client):
    db = client["ObesityDataSet"]

    # Crear colecciones si no existen
    def ensure_collections():
        if "users" not in db.list_collection_names():
            db.create_collection("users")
        if "reports" not in db.list_collection_names():
            db.create_collection("reports")


    ensure_collections()

    users_collection = db["users"]
    reports_collection = db["reports"]
    return db, users_collection, reports_collection
