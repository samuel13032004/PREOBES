import pymongo
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import MinMaxScaler

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

    data = list(collection.find())
    df = pd.DataFrame(data)

    if "_id" in df.columns:
        df = df.drop(columns=["_id"])

    df['IMC'] = df['Weight'] / (df['Height'] ** 2)

    categorical_columns = ['Gender', 'family_history_with_overweight', 'FAVC', 'CAEC',
                           'SMOKE', 'SCC', 'CALC', 'MTRANS']

    for col in categorical_columns:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col])

    X = df.drop(columns=["NObeyesdad"])
    y = df["NObeyesdad"]

    return df, X, y


df, X, y = cargar_datos()


def cargar_datos_mongo(client):
    db = client["ObesityDataSet"]

    def ensure_collections():
        if "users" not in db.list_collection_names():
            db.create_collection("users")
        if "reports" not in db.list_collection_names():
            db.create_collection("reports")

    ensure_collections()
    db_collection = db["ObesityDataSet"]
    users_collection = db["users"]
    reports_collection = db["reports"]
    return db, db_collection, users_collection, reports_collection
