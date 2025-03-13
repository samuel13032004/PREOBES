from flask import Flask, render_template, request
import pickle
import pandas as pd
import numpy as np
import os
from openai import OpenAI

app = Flask(__name__)

# Configurar la API key de OpenAI
client = OpenAI(api_key=os.getenv("apikey"))

# Cargar el modelo, scaler, label encoder y la lista de columnas preprocesadas
with open("resultados_modelo/modelo_obesidad.pkl", "rb") as f:
    modelo_tuple = pickle.load(f)
    # Si el modelo es una tupla, tomamos el primer elemento que debería ser el modelo real
    if isinstance(modelo_tuple, tuple):
        modelo = modelo_tuple[0]
    else:
        modelo = modelo_tuple

with open("resultados_modelo/scaler.pkl", "rb") as f:
    scaler = pickle.load(f)

with open("resultados_modelo/label_encoder.pkl", "rb") as f:
    le = pickle.load(f)

with open("resultados_modelo/columns.pkl", "rb") as f:
    model_columns = pickle.load(f)

@app.route('/')
def index():
    return render_template('form.html')


def get_ai_recommendation(user_data, prediction, imc):
    """
    Genera recomendaciones personalizadas usando la API de OpenAI
    basadas en los datos del usuario y la predicción
    """
    # Convertir datos numéricos a valores legibles
    age = user_data.get('Age')
    height = user_data.get('Height')
    weight = user_data.get('Weight')
    gender = user_data.get('Gender')
    family_history = "Sí" if user_data.get('family_history') == 'yes' else "No"
    favc = "Sí" if user_data.get('FAVC') == 'yes' else "No"
    smoke = "Sí" if user_data.get('SMOKE') == 'yes' else "No"
    physical_activity = user_data.get('FAF', '0')

    # Mapeo de categorías de predicción
    prediction_mapping = {
        "Insufficient_Weight": "Peso Insuficiente",
        "Normal_Weight": "Peso Normal",
        "Overweight_Level_I": "Sobrepeso Nivel I",
        "Overweight_Level_II": "Sobrepeso Nivel II",
        "Obesity_Type_I": "Obesidad Tipo I",
        "Obesity_Type_II": "Obesidad Tipo II",
        "Obesity_Type_III": "Obesidad Tipo III"
    }

    prediction_es = prediction_mapping.get(prediction, prediction)

    # Crear prompt para OpenAI
    prompt = f"""
    Actúa como un experto nutricionista y entrenador personal. Genera recomendaciones personalizadas para una persona con las siguientes características:

    - Género: {gender}
    - Edad: {age} años
    - Altura: {height} metros
    - Peso: {weight} kg
    - IMC: {imc}
    - Historial familiar de obesidad: {family_history}
    - Consume frecuentemente alimentos altos en calorías: {favc}
    - Fumador: {smoke}
    - Nivel de actividad física (0-3, donde 0 es sedentario y 3 es muy activo): {physical_activity}

    El diagnóstico de esta persona es: {prediction_es}

    Proporciona recomendaciones personalizadas en 3-4 párrafos que incluyan:
    1. Una explicación breve y clara de lo que significa su categoría de peso
    2. Consejos de alimentación específicos 
    3. Recomendaciones de actividad física apropiadas
    4. Cambios de hábitos que podrían beneficiarle

    Usa un tono profesional pero amigable. Las recomendaciones deben ser realistas y específicas para su condición.
    """

    try:
        # Llamada a la API de OpenAI
        response = client.chat.completions.create(
            model="gpt-4",  # Puedes usar gpt-3.5-turbo si prefieres
            messages=[
                {"role": "system", "content": "Eres un asistente especializado en nutrición y salud."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.2
        )

        # Extraer la recomendación del resultado
        recommendation = response.choices[0].message.content.strip()
        return recommendation

    except Exception as e:
        print(f"Error al llamar a la API de OpenAI: {e}")
        # Si hay error, retornamos un mensaje genérico
        return f"""
        Lo sentimos, no pudimos generar recomendaciones personalizadas en este momento.

        Su diagnóstico es {prediction_es} con un IMC de {imc}.

        Le recomendamos consultar con un profesional de la salud para obtener orientación específica para su condición.
        """


@app.route('/predict', methods=['POST'])
def predict():
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

    # Calcular IMC explícitamente
    input_df['IMC'] = input_df['Weight'] / (input_df['Height'] ** 2)
    imc_value = round(input_df['IMC'].values[0], 2)

    # Aplicar one-hot encoding de forma similar a como se hizo en el entrenamiento
    input_processed = pd.get_dummies(input_df, drop_first=True)

    # Alinear las columnas del input con las columnas usadas en el entrenamiento
    missing_cols = set(model_columns) - set(input_processed.columns)
    for col in missing_cols:
        input_processed[col] = 0

    # Asegurar el mismo orden de columnas
    input_processed = input_processed[model_columns]

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

    # Obtener recomendaciones personalizadas de la IA
    ai_recommendation = get_ai_recommendation(form_data, pred_label, imc_value)

    return render_template(
        'result.html',
        prediction=pred_label,
        imc=imc_value,
        probabilities=sorted_probabilities,
        ai_recommendation=ai_recommendation  # Pasar la recomendación personalizada a la plantilla
    )


if __name__ == '__main__':
    app.run(debug=True)
