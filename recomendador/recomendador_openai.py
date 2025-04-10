import requests
from flask import session
from datetime import datetime


def calcular_edad(fecha_nacimiento):
    """
    Calcula la edad a partir de la fecha de nacimiento (YYYY-MM-DD).
    """
    fecha_nacimiento = datetime.strptime(fecha_nacimiento, "%Y-%m-%d")
    hoy = datetime.today()
    edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
    return edad


def calcular_edad_en_fecha(birthdate: str, report_date: str) -> int:
    """ Calcula la edad de una persona en la fecha de un informe. """
    birth_date = datetime.strptime(birthdate, "%Y-%m-%d")  # Convierte birthdate a objeto datetime
    report_date = datetime.strptime(report_date, "%Y-%m-%d")  # Convierte report_date a objeto datetime

    edad = report_date.year - birth_date.year - (
                (report_date.month, report_date.day) < (birth_date.month, birth_date.day))
    return edad


def get_ai_recommendation(user_data, prediction, imc, reports_collection, token_openai):
    """
    Genera recomendaciones personalizadas usando la API de OpenAI
    basadas en los datos del usuario y la predicción
    """
    # Convertir datos numéricos a valores legibles
    user_id = session.get('user_id')

    birthdate = user_data.get('birthdate')
    age = calcular_edad(birthdate) if birthdate else "No especificado"

    height = user_data.get('Height')
    weight = user_data.get('Weight')
    gender = user_data.get('Gender')

    # Conversión de parámetros booleanos
    family_history = "Sí" if user_data.get('family_history') == 'yes' else "No"
    favc = "Sí" if user_data.get('FAVC') == 'yes' else "No"
    smoke = "Sí" if user_data.get('SMOKE') == 'yes' else "No"

    # Extracción de parámetros adicionales
    physical_activity = user_data.get('FAF', '0')
    water_consumption = user_data.get('CH2O', 'No especificado')
    alcohol_consumption = user_data.get('CALC', 'No especificado')
    meal_frequency = user_data.get('NCP', 'No especificado')
    vegetable_frequency = user_data.get('FCVC', 'No especificado')
    tech_usage_time = user_data.get('TUE', 'No especificado')
    transport_method = user_data.get('MTRANS', 'No especificado')
    calorie_control = user_data.get('SCC', 'No especificado')

    # Obtener reportes previos de la base de datos
    previous_reports = reports_collection.find({"user_id": user_id}).sort("date", -1).limit(5)  # 5 últimos informes

    field_mapping = {
        "Height": "Altura",
        "Weight": "Peso",
        "family_history": "Historial familiar de obesidad",
        "FAVC": "Consumo frecuente de alimentos altos en calorías",
        "FCVC": "Frecuencia de consumo de vegetales",
        "NCP": "Número de comidas por día",
        "CAEC": "Consumo de comida entre comidas",
        "CH2O": "Consumo de agua diario",
        "SCC": "Control de calorías en la dieta",
        "FAF": "Nivel de actividad física (0-4)",
        "MTRANS": "Medio de transporte principal",
        "TUE": "Tiempo de uso de tecnología",
        "CALC": "Consumo de alcohol",
        "SMOKE": "Fumador"
    }

    # Crear un resumen de los reportes previos
    previous_reports_summary = ""
    for report in previous_reports:
        report_number = report['report_number']
        report_date = report['date'].strftime("%Y-%m-%d %H:%M:%S")
        report_date_2 = report['date'].strftime("%Y-%m-%d")
        report_imc = report['imc']
        report_prediction = report['prediction']
        report_age = calcular_edad_en_fecha(user_data.get('birthdate'), report_date_2)

        # Filtrar los datos personales antes de incluir form_data
        report_form_data = report.get('form_data', {})
        filtered_form_data = {k: v for k, v in report_form_data.items() if
                              k not in ['user_id', 'Name', 'Surname', 'Gender', 'birthdate', 'age']}

        formatted_form_data = "\n  * " + "\n  * ".join(
            f"{field_mapping.get(k, k)}: {v}" for k, v in filtered_form_data.items()
        )

        # Construir una cadena con los detalles del reporte
        previous_reports_summary += f"""
Reporte {report_number} (Fecha: {report_date}):
- Edad en el informe: {report_age} años
- IMC: {report_imc}
- Diagnóstico: {report_prediction}
- Datos del Formulario: {formatted_form_data}
            """

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

    prompt = f"""
    Eres un experto nutricionista y entrenador personal español. Genera recomendaciones personalizadas 
    para una persona con las siguientes características:

    Datos Personales:
    - Género: {gender}
    - Edad: {age} años
    - Altura: {height} metros
    - Peso: {weight} kg
    - IMC: {imc}

    Historial y Hábitos:
    - Historial familiar de obesidad: {family_history}
    - Consume frecuentemente alimentos altos en calorías: {favc}
    - Fumador: {smoke}
    - Nivel de actividad física (0-4, donde 0 es sedentario y 4 es muy activo): {physical_activity}
    - Consumo de agua diario: {water_consumption} litros
    - Frecuencia de consumo de vegetales (ten en cuenta que 1 es el mínimo y 3 el máximo): {vegetable_frequency}
    - Número de comidas por día: {meal_frequency}
    - Consumo de alcohol: {alcohol_consumption}
    - Tiempo de uso de tecnología (horas al día): {tech_usage_time}
    - Medio de transporte principal: {transport_method}
    - Control de calorías: {calorie_control}

    El diagnóstico actual de esta persona es: {prediction_es}
    """

    prompt += f"""
    Proporciona recomendaciones personalizadas (CRÍTICO: No numeres los párrafos en la respuesta) basadas en el informe 
    más reciente rellenado por el usuario en 3-4 párrafos separados por saltos de líneas que incluyan:
    1. Una explicación breve y clara de lo que significa su categoría de peso.
    2. Consejos de alimentación específicos, resaltando los buenos hábitos alimenticios en caso de tenerlos.
    3. Recomendaciones de actividad física apropiadas, resaltando los buenos hábitos en caso de haberlos.
    4. Cambios de hábitos que podrían beneficiarle (en caso de que hayan). 

    Usa un tono profesional pero amigable. Las recomendaciones deben ser realistas y específicas para su condición.
    """

    if len(previous_reports_summary) > 0:
        prompt += f"""
        Informes Previos:
        {previous_reports_summary}

        Por último, analiza la evolución del usuario comparando sus datos actuales con los informes previos. 
        Evalúa si ha mejorado sus hábitos o si algunos se han empeorado, y destaca aquellos hábitos que necesitan 
        atención o cambio para mejorar su salud. Si la evolución ha sido 
        favorable, felicita al usuario resaltando sus logros y mejoras; si ha sido desfavorable, proporciona comentarios 
        constructivos y sugerencias para mejorar, siempre en un tono respetuoso y profesional.
        """

    print(prompt)
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "gemma3",
            "prompt": prompt,
            "temperature": 0.2,
            "stream": False
        }
    )

    if response.status_code == 200:
        contenido = response.json()["response"].strip()
        print(contenido)
        return contenido
    else:
        print("Error al generar la recomendación:", response.status_code, response.text)
        return None