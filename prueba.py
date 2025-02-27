import pymongo
import pandas as pd
import numpy as np
import pickle


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


# 3. Seleccionar variables predictoras y variable objetivo
# Se asume que el DataFrame contiene una columna 'Obesity_Level' con las etiquetas:
# "Insufficient Weight", "Normal Weight", "Overweight Level I", "Overweight Level II",
# "Obesity Type I", "Obesity Type II", "Obesity Type III"
X = df.drop(columns=["NObeyesdad"])
y = df["NObeyesdad"]


# 4. Preprocesamiento
# Convertir variables categóricas a variables dummy (one-hot encoding) si es necesario
X = pd.get_dummies(X, drop_first=True)


# Codificar la variable objetivo a valores numéricos
le = LabelEncoder()
y_encoded = le.fit_transform(y)


# Dividir el dataset en conjuntos de entrenamiento y prueba
X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)


# Escalar las características numéricas
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)


# 5. Entrenar el modelo predictivo
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train_scaled, y_train)


# 6. Realizar predicciones y evaluar el modelo
y_pred = clf.predict(X_test_scaled)
accuracy = accuracy_score(y_test, y_pred)
report = classification_report(y_test, y_pred, target_names=le.classes_)


print("\nExactitud del modelo:", accuracy)
print("\nReporte de clasificación:")
print(report)


importances = clf.feature_importances_
indices = np.argsort(importances)[::-1]
print("Importancia de las características:")
for i in range(len(indices)):
   print(f"{X.columns[indices[i]]}: {importances[indices[i]]:.4f}")


# Guarda el modelo entrenado
with open("modelo_obesidad.pkl", "wb") as f:
   pickle.dump(clf, f)


# Guarda el scaler
with open("scaler.pkl", "wb") as f:
   pickle.dump(scaler, f)


# Guarda el label encoder
with open("label_encoder.pkl", "wb") as f:
   pickle.dump(le, f)


# Guarda las columnas resultantes de X tras aplicar get_dummies
with open("columns.pkl", "wb") as f:
   pickle.dump(X.columns.tolist(), f)
