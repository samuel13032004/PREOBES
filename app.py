from flask import Flask
import os
import pymongo

from cargar_datos.cargar_datos_mongodb import cargar_datos_mongo
from rutas_backend.rutas import configurar_rutas_configuracion
from utilidades.modelos import cargar_modelos
app = Flask(__name__)
app.config['DEBUG'] = True  # Enable debugging in development
app.secret_key = 'your_secret_key_here'  # Replace with a strong secret key

modelo, scaler, le, model_columns = cargar_modelos()
token_openai = api_key=os.getenv("apikey")
client = pymongo.MongoClient("mongodb://localhost:27017/")
db, users_collection, reports_collection = cargar_datos_mongo(client)
configurar_rutas_configuracion(app, modelo, scaler, le, model_columns, users_collection, reports_collection,token_openai)


if __name__ == '__main__':
    app.run(debug=True)
