import pymongo
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score


# 1. Conectar a MongoDB
# Asegúrate de que el servicio de MongoDB esté corriendo (generalmente en localhost:27017)
client = pymongo.MongoClient("mongodb://localhost:27017/")


# Reemplaza "mi_basededatos" por el nombre de tu base de datos
db = client["ObesityDataSet"]


# Reemplaza "mi_coleccion" por el nombre de la colección donde tienes tus datos
collection = db["ObesityDataSet"]


# 2. Extraer los datos de la colección
data = list(collection.find())
df = pd.DataFrame(data)


# Si existe el campo '_id' que MongoDB agrega por defecto, lo eliminamos para el análisis
if "_id" in df.columns:
   df = df.drop(columns=["_id"])


# Visualizar información básica del dataset
print("Primeras filas del dataset:")
print(df.head())
print("\nInformación del dataset:")
print(df.info())


# Convertir variables categóricas en variables numéricas
categorical_columns = ['Gender', 'family_history_with_overweight', 'FAVC', 'CAEC', 'SMOKE', 'SCC', 'CALC', 'MTRANS']
for col in categorical_columns:
   le = LabelEncoder()
   df[col] = le.fit_transform(df[col])


# Separar las características (X) y la variable objetivo (y)
X = df.drop(columns=["NObeyesdad"])  # Reemplaza 'NObeyesdad' con el nombre de la columna objetivo
y = df["NObeyesdad"]


# Estandarización de los datos
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)


# Dividir los datos en conjunto de entrenamiento y prueba
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)


# Modelo de Random Forest
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)


# Evaluación del modelo
y_pred = model.predict(X_test)
print("Informe de clasificación:\n", classification_report(y_test, y_pred))
print("Precisión del modelo:", accuracy_score(y_test, y_pred))


# TODO Es necesario quitar el peso y hacer la probabilidad sobre 100




# Importancia de las variables
feature_importances = pd.DataFrame(model.feature_importances_,
                                  index=X.columns,
                                  columns=["Importancia"]).sort_values("Importancia", ascending=False)


print("Importancia de las variables:")
print(feature_importances)



