from flask import Flask, render_template, request
import pickle
import pandas as pd
import numpy as np

app = Flask(__name__)

# Cargar el modelo, scaler, label encoder y la lista de columnas preprocesadas
try:
    with open("modelo_obesidad.pkl", "rb") as f:
        modelo, le, scaler = pickle.load(f)

    with open("columns.pkl", "rb") as f:
        model_columns = pickle.load(f)

    print("Modelo cargado correctamente")
except Exception as e:
    print(f"Error al cargar el modelo: {e}")
    # Definir variables vacías para evitar errores al iniciar la aplicación
    modelo, le, scaler, model_columns = None, None, None, None


@app.route('/')
def index():
    return render_template('form.html')


@app.route('/predict', methods=['POST'])
def predict():
    if modelo is None or le is None or scaler is None:
        return render_template('error.html', message="El modelo no se ha cargado correctamente")

    try:
        # Recoger los datos del formulario
        form_data = request.form.to_dict()

        # Asegurarse de que todos los campos necesarios existen
        required_fields = [
            'Gender', 'Age', 'Height', 'Weight', 'family_history', 'FAVC',
            'FCVC', 'NCP', 'CAEC', 'SMOKE', 'CH2O', 'SCC', 'FAF',
            'TUE', 'CALC', 'MTRANS'
        ]

        for field in required_fields:
            if field not in form_data:
                # Valores predeterminados apropiados para cada campo
                if field in ['Age', 'Height', 'Weight', 'FCVC', 'NCP', 'CH2O', 'FAF', 'TUE']:
                    form_data[field] = '0'  # Valores numéricos como string
                else:
                    form_data[field] = 'no'  # Valores categóricos

        # Convertir el diccionario a DataFrame
        input_df = pd.DataFrame([form_data])

        # Convertir los campos numéricos conocidos a valores numéricos
        numeric_cols = ['Age', 'Height', 'Weight', 'FCVC', 'NCP', 'CH2O', 'FAF', 'TUE']
        for col in numeric_cols:
            if col in input_df.columns:
                input_df[col] = pd.to_numeric(input_df[col], errors='coerce')

        # Verificar datos numéricos y manejar valores no válidos
        if input_df['Height'].values[0] <= 0 or input_df['Weight'].values[0] <= 0:
            return render_template('error.html',
                                   message="La altura y el peso deben ser valores positivos")

        # Calcular IMC explícitamente
        input_df['IMC'] = input_df['Weight'] / ((input_df['Height'] / 100) ** 2)  # Altura en cm a metros

        # Información de diagnóstico
        print(f"Datos recibidos: {form_data}")
        print(f"IMC calculado: {input_df['IMC'].values[0]}")

        # Aplicar one-hot encoding
        input_processed = pd.get_dummies(input_df)

        # Alinear las columnas del input con las columnas usadas en el entrenamiento
        for col in model_columns:
            if col not in input_processed.columns:
                input_processed[col] = 0

        # Asegurar el mismo orden de columnas y seleccionar solo las necesarias
        input_processed = input_processed.reindex(columns=model_columns, fill_value=0)

        # Escalar los datos
        input_scaled = scaler.transform(input_processed)

        # Realizar la predicción
        pred_num = modelo.predict(input_scaled)
        pred_label = le.inverse_transform(pred_num)[0]

        # Obtener probabilidades para cada clase
        pred_proba = modelo.predict_proba(input_scaled)[0]
        class_probabilities = {le.inverse_transform([i])[0]: round(prob * 100, 2)
                               for i, prob in enumerate(pred_proba)}

        # Ordenar probabilidades de mayor a menor
        sorted_probabilities = sorted(class_probabilities.items(),
                                      key=lambda x: x[1],
                                      reverse=True)


        return render_template(
            'result.html',
            prediction=pred_label,
            imc=round(input_df['IMC'].values[0], 2),
            probabilities=sorted_probabilities
        )

    except Exception as e:
        print(f"Error durante la predicción: {e}")
        return render_template('error.html', message=f"Error al procesar la solicitud: {str(e)}")


# Plantilla básica de error para manejo de excepciones
@app.route('/error')
def error():
    message = request.args.get('message', 'Ha ocurrido un error desconocido')
    return render_template('error.html', message=message)


if __name__ == '__main__':
    app.run(debug=True)
