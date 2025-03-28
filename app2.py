from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

from flask import Flask, render_template, request, send_file, jsonify
import pickle
import pandas as pd
import numpy as np
import os
from openai import OpenAI
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from io import BytesIO
from datetime import datetime, time
import pymongo

app = Flask(__name__)

client = pymongo.MongoClient("mongodb://localhost:27017/")
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
    return render_template('login.html')


def calcular_edad(fecha_nacimiento):
    """
    Calcula la edad a partir de la fecha de nacimiento (YYYY-MM-DD).
    """
    fecha_nacimiento = datetime.strptime(fecha_nacimiento, "%Y-%m-%d")
    hoy = datetime.today()
    edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
    return edad


def get_ai_recommendation(user_data, prediction, imc):
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
        report_imc = report['imc']
        report_prediction = report['prediction']

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
    Actúa como un experto nutricionista y entrenador personal. Genera recomendaciones personalizadas para una persona 
    con las siguientes características:

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
    - Frecuencia de consumo de vegetales: {vegetable_frequency}
    - Número de comidas por día: {meal_frequency}
    - Consumo de alcohol: {alcohol_consumption}
    - Tiempo de uso de tecnología: {tech_usage_time}
    - Medio de transporte principal: {transport_method}
    - Control de calorías: {calorie_control}

    El diagnóstico actual de esta persona es: {prediction_es}


    Informes Previos:
    {previous_reports_summary}

    Proporciona recomendaciones personalizadas basadas en el informe más reciente rellenado por el usuario en 3-4 
    párrafos que incluyan:
    1. Una explicación breve y clara de lo que significa su categoría de peso.
    2. Consejos de alimentación específicos.
    3. Recomendaciones de actividad física apropiadas.
    4. Cambios de hábitos que podrían beneficiarle.

    Por último, analiza la evolución del usuario comparando sus datos actuales con los informes previos. 
    Evalúa si ha mejorado sus hábitos o si algunos se han empeorado, y destaca aquellos hábitos que necesitan atención 
    o cambio para mejorar su salud. Si la evolución ha sido 
    favorable, felicita al usuario resaltando sus logros y mejoras; si ha sido desfavorable, proporciona comentarios 
    constructivos y sugerencias para mejorar, siempre en un tono respetuoso y profesional. 

    Usa un tono profesional pero amigable. Las recomendaciones deben ser realistas y específicas para su condición.
    """

    print(prompt)
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
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


def create_pdf_report(user_data, prediction, imc, probabilities, ai_recommendation):
    """
    Crea un informe en PDF con los resultados del análisis y recomendaciones
    Añade iconos y mejora el diseño visual
    """
    # Crear un buffer en memoria para el PDF
    buffer = BytesIO()

    # Crear el documento PDF con márgenes más generosos
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=50, leftMargin=50,
                            topMargin=50, bottomMargin=30)

    # Estilos para el PDF
    styles = getSampleStyleSheet()

    # Personalizar estilos existentes
    styles['Title'].fontSize = 18
    styles['Title'].textColor = colors.HexColor('#1A5F7A')  # Color azul profesional
    styles['Title'].alignment = TA_CENTER
    styles['Title'].spaceAfter = 18

    # Estilos personalizados con más variedad
    styles.add(ParagraphStyle(name='SubtitleWithIcon',
                              fontName='Helvetica-Bold',
                              fontSize=14,
                              textColor=colors.HexColor('#2C7DA0'),
                              spaceAfter=10))

    styles.add(ParagraphStyle(name='CustomNormal',
                              fontName='Helvetica',
                              fontSize=11,
                              alignment=TA_JUSTIFY,
                              spaceAfter=8))

    # Elementos del PDF
    elements = []

    elements.append(Paragraph("Informe de Evaluación de Riesgo de Obesidad", styles['Title']))

    # Título con icono 📊
    # Cargar la imagen del icono "finance-and-business.png"
    icon_path = "iconos/finance-and-business.png"  # Ruta de la imagen
    img = Image(icon_path, width=20, height=20)  # Ajusta el tamaño según sea necesario

    # Cargar la imagen del icono "calendar.png"
    icon_path_calendar = "iconos/calendar.png"  # Ruta de la imagen
    img_calendar = Image(icon_path_calendar, width=20, height=20)

    # Fecha con icono 📅
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
    fecha_paragraph = Paragraph(f"Fecha de generación: {fecha_actual}", styles['Normal'])

    # Crear una tabla con una fila que contenga la imagen y la fecha juntos
    data_fecha = [[img_calendar, fecha_paragraph]]
    table_fecha = Table(data_fecha, colWidths=[50, 400])  # Ajusta el tamaño de las columnas si es necesario

    # Establecer estilo para la tabla (sin bordes)
    table_fecha.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    # Añadir la tabla con la imagen y la fecha al documento
    elements.append(table_fecha)
    elements.append(Spacer(1, 15))

    # Mapeo de categorías con emojis
    prediction_mapping = {
        "Insufficient_Weight": "🟢 Peso Insuficiente",
        "Normal_Weight": "🟢 Peso Normal",
        "Overweight_Level_I": "🟠 Sobrepeso Nivel I",
        "Overweight_Level_II": "🟠 Sobrepeso Nivel II",
        "Obesity_Type_I": "🔴 Obesidad Tipo I",
        "Obesity_Type_II": "🔴 Obesidad Tipo II",
        "Obesity_Type_III": "🔴 Obesidad Tipo III"
    }
    prediction_es = prediction_mapping.get(prediction, prediction)

    # Datos personales con icono 👤
    # Cargar la imagen del icono "user.png"
    icon_path_user = "iconos/user.png"  # Ruta de la imagen
    img_user = Image(icon_path_user, width=20, height=20)  # Ajusta el tamaño según sea necesario

    # Título de "Datos personales" con el icono
    data_user = [[img_user, Paragraph("Datos personales", styles['SubtitleWithIcon'])]]
    table_user = Table(data_user, colWidths=[50, 400])  # Ajusta el tamaño de las columnas si es necesario

    # Establecer estilo para la tabla (sin bordes)
    table_user.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    # Añadir la tabla con el icono y el texto al documento
    elements.append(table_user)
    elements.append(Spacer(1, 15))

    # Convertir datos a formato legible para el informe
    gender = "Masculino" if user_data.get('Gender') == 'Male' else "Femenino"
    family_history = "Sí" if user_data.get('family_history') == 'yes' else "No"
    favc = "Sí" if user_data.get('FAVC') == 'yes' else "No"
    smoke = "Sí" if user_data.get('SMOKE') == 'yes' else "No"
    birthdate = user_data.get('birthdate')
    age = calcular_edad(birthdate) if birthdate else "No especificado"

    # Actividad física
    faf_mapping = {
        "0": "Sedentario",
        "1": "Ligero",
        "2": "Moderado",
        "3": "Intenso"
    }
    physical_activity = faf_mapping.get(user_data.get('FAF', '0'), "No especificado")

    existing_user = users_collection.find_one({"name": user_data.get('Name'), "surname": user_data.get('Surname')})
    user_id = existing_user["user_id"]
    report_number = existing_user["report_count"]
    print(f"ID de usuario: {user_id}")
    # Tabla de datos personales
    data = [
        ["ID Usuario", user_id],
        ["NºInforme", report_number],
        ["Nombre", user_data.get('Name')],
        ["Apellidos", user_data.get('Surname')],
        ["Género", gender],
        ["Edad", f"{age} años"],
        ["Altura", f"{user_data.get('Height')} metros"],
        ["Peso", f"{user_data.get('Weight')} kg"],
        ["IMC", f"{imc}"],
        ["Historial familiar de obesidad", family_history],
        ["Consumo frecuente de calorías", favc],
        ["Fumador", smoke],
        ["Nivel de actividad física", physical_activity]
    ]

    t = Table(data, colWidths=[200, 200])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(t)
    elements.append(Spacer(1, 12))

    # Resultado de la evaluación con icono 📋
    # Cargar la imagen del icono "contract.png"
    icon_path = "iconos/contract.png"  # Ruta de la imagen
    img = Image(icon_path, width=20, height=20)  # Ajusta el tamaño según sea necesario

    # Crear la tabla con el icono y el texto "Resultado de la Evaluación"
    data_resultado = [[img, Paragraph("Resultado de la Evaluación", styles['SubtitleWithIcon'])]]
    table_resultado = Table(data_resultado, colWidths=[25, 400])  # Ajusta el tamaño de las columnas si es necesario

    # Establecer estilo para la tabla (sin bordes)
    table_resultado.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    # Añadir la tabla con el icono y el texto al documento
    elements.append(table_resultado)
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Su nivel de riesgo es: <b>{prediction_es}</b>", styles['CustomNormal']))
    elements.append(Paragraph(f"Índice de Masa Corporal (IMC): <b>{imc}</b>", styles['CustomNormal']))

    icon_path = "iconos/finance-and-business.png"  # Ruta de la imagen
    img = Image(icon_path, width=20, height=20)  # Ajusta el tamaño según sea necesario

    # Crear la tabla con el icono y el texto "Desglose de probabilidades"
    data_probabilities = [[img, Paragraph("Desglose de probabilidades:", styles['SubtitleWithIcon'])]]
    table_probabilities = Table(data_probabilities,
                                colWidths=[25, 400])  # Ajusta el tamaño de las columnas si es necesario

    # Establecer estilo para la tabla (sin bordes)
    table_probabilities.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    # Añadir la tabla con el icono y el texto al documento
    elements.append(table_probabilities)
    elements.append(Spacer(1, 15))
    prob_data = [["Categoría", "Probabilidad (%)"]]

    # Traducir nombres de categorías
    for category, prob in probabilities:
        category_es = prediction_mapping.get(category, category)
        prob_data.append([category_es, f"{prob}%"])

    prob_table = Table(prob_data, colWidths=[300, 100])
    prob_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(prob_table)
    elements.append(Spacer(1, 12))

    # Recomendaciones personalizadas
    # Cargar la imagen del icono "lamp.png"
    icon_path_lamp = "iconos/lamp.png"  # Ruta de la imagen
    img_lamp = Image(icon_path_lamp, width=20, height=20)  # Ajusta el tamaño según sea necesario

    # Crear la tabla con el icono y el texto "Recomendaciones Personalizadas"
    data_recomendaciones = [[img_lamp, Paragraph("Recomendaciones Personalizadas", styles['SubtitleWithIcon'])]]
    table_recomendaciones = Table(data_recomendaciones,
                                  colWidths=[25, 400])  # Ajusta el tamaño de las columnas si es necesario

    # Establecer estilo para la tabla (sin bordes)
    table_recomendaciones.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    # Añadir la tabla con el icono y el texto al documento
    elements.append(table_recomendaciones)
    elements.append(Spacer(1, 12))

    # Procesar párrafos de recomendaciones
    for paragraph in ai_recommendation.split('\n\n'):
        if paragraph.strip():
            elements.append(Paragraph(paragraph.strip(), styles['CustomNormal']))

    elements.append(Spacer(1, 12))

    icon_path_warning = "iconos/warning.png"  # Ruta de la imagen
    img_warning = Image(icon_path_warning, width=20, height=20)  # Ajusta el tamaño según sea necesario

    # Crear la tabla con el icono y el texto "Disclaimer"
    data_disclaimer = [
        [img_warning, Paragraph("<i>Este informe es generado automáticamente y tiene fines informativos. " +
                                "No reemplaza el consejo de un profesional de la salud. " +
                                "Consulte siempre con su médico o nutricionista antes de implementar cambios " +
                                "significativos en su dieta o régimen de actividad física.</i>", styles['Normal'])]]
    table_disclaimer = Table(data_disclaimer, colWidths=[25, 400])  # Ajusta el tamaño de las columnas si es necesario

    # Establecer estilo para la tabla (sin bordes)
    table_disclaimer.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    # Añadir la tabla con el icono y el texto al documento
    elements.append(table_disclaimer)
    # Generar el PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


@app.route('/predict', methods=['POST'])
def predict():
    # Recoger los datos del formulario
    form_data = request.form.to_dict()
    user_id = session.get('user_id')
    if not user_id:
        flash('No estás autenticado. Por favor, inicia sesión.', 'error')
        return redirect(url_for('login'))

    # Verificar si el usuario ya existe en la BD
    existing_user = users_collection.find_one({"user_id": user_id})
    if existing_user:
        user_id = existing_user["user_id"]
        report_number = existing_user["report_count"] + 1
        users_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"report_count": 1}}
        )

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

    # Guardar los datos de la sesión para la descarga del PDF
    # Esto normalmente se haría con una base de datos o sesiones,
    # pero para simplificar usaremos variables globales
    app.config['LAST_PREDICTION'] = {
        'form_data': form_data,
        'prediction': pred_label,
        'imc': imc_value,
        'probabilities': sorted_probabilities,
        'ai_recommendation': ai_recommendation
    }

    # Guardar en la BD el informe del usuario
    report_entry = {
        "user_id": user_id,
        "report_number": report_number,
        "date": datetime.now(),
        "imc": imc_value,
        "prediction": pred_label,
        "probabilities": {le.inverse_transform([i])[0]: round(prob * 100, 2) for i, prob in enumerate(pred_proba)},
        "form_data": form_data  # Guardar todos los datos del usuario en el informe
    }
    reports_collection.insert_one(report_entry)

    return render_template(
        'result.html',
        prediction=pred_label,
        imc=imc_value,
        probabilities=sorted_probabilities,
        ai_recommendation=ai_recommendation
    )


@app.route('/download-report')
def download_report():
    """
    Genera y descarga un informe PDF con los resultados de la evaluación
    """
    # Recuperar los datos de la última predicción
    last_prediction = app.config.get('LAST_PREDICTION')

    if not last_prediction:
        # Si no hay datos, redirigir a la página principal
        return "No hay datos disponibles para generar el informe. Por favor, realice una evaluación primero.", 400

    # Crear el PDF
    pdf_buffer = create_pdf_report(
        last_prediction['form_data'],
        last_prediction['prediction'],
        last_prediction['imc'],
        last_prediction['probabilities'],
        last_prediction['ai_recommendation']
    )

    # Generar un nombre de archivo con la fecha actual
    filename = f"informe_obesidad_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    # Enviar el archivo al usuario
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )


@app.route('/evolucion-data')
def evolucion_data():
    # user_id = request.args.get("user_id", type=int)

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "You need to log in to access this data"}), 401

    variable = request.args.get("variable")  # Por defecto IMC

    reports = list(reports_collection.find({"user_id": user_id}).sort("report_number", 1))

    if not reports:
        return jsonify({"error": "No se encontraron informes para este usuario"}), 404

    report_numbers = [r["report_number"] for r in reports]

    categorical_variables = {
        "FAVC": ["no", "yes"],
        "CAEC": ["no", "Sometimes", "Frequently", "Always"],
        "SMOKE": ["no", "yes"],
        "SCC": ["no", "yes"],
        "CALC": ["No", "Sometimes", "Frequently", "Always"],
        "MTRANS": ["Public_Transportation", "Walking", "Automobile", "Motorbike", "Bike"],
        "prediction": ["Insufficient_Weight", "Normal_Weight", "Overweight_Level_I", "Overweight_Level_II",
                       "Obesity_Type_I", "Obesity_Type_II", "Obesity_Type_III"],
        "FAF": ["0", "1", "2", "3", "4"],
        "NCP": ["1", "2", "3", "4"],
        "FCVC": ["1", "2", "3"]
    }

    variable_values = []
    is_categorical = variable in categorical_variables
    categories = categorical_variables.get(variable, [])

    for r in reports:
        value = None
        if variable in r:
            value = r.get(variable)
        elif "form_data" in r and variable in r["form_data"]:
            value = r["form_data"].get(variable)

        if is_categorical:
            # Convertir el valor a su índice dentro de la lista de categorías
            value = categories.index(value) if value in categories else None
        else:
            value = float(value) if isinstance(value, (int, float, str)) and str(value).replace('.', '',
                                                                                                1).isdigit() else 0

        variable_values.append(value)

    print(variable_values)
    variable_labels = {
        "imc": "Índice de Masa Corporal (IMC)",
        "prediction": "Niveles de Obesidad",
        "Weight": "Peso (kg)",
        "CH2O": "Consumo de Agua (Litros)",
        "FAF": "Frecuencia de Actividad Física",
        "TUE": "Tiempo de Uso de Tecnologías (TUE)",
        "CALC": "Consumo de Alcohol (CALC)",
        "CAEC": "Alimentos entre Horas (CAEC)",
        "MTRANS": "Medio de Transporte (MTRANS)",
        "NCP": "Número de Comidas por Día (NCP)",
        "FCVC": "Frecuencia de Consumo de Verduras (FCVC)",
        "SMOKE": "Fuma (SMOKE)",
        "FAVC": "Alimentos ricos en calorías (FAVC)",
        "SCC": "Control de Calorías"
    }

    return jsonify({
        "report_numbers": report_numbers,
        "variable_name": variable_labels.get(variable, variable),
        "variable_values": variable_values,
        "is_categorical": is_categorical,
        "categories": categories
    })


app.secret_key = 'your_secret_key_here'  # Replace with a strong secret key


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        surname = request.form['surname']
        Gender = request.form['Gender']
        birthdate = request.form['birthdate']
        # Check if user already exists
        existing_user = users_collection.find_one({"username": username})
        if existing_user:
            flash('Username already exists. Please choose another.', 'error')
            return redirect(url_for('register'))

        # Generate a unique user ID
        last_user = users_collection.find_one(sort=[("user_id", -1)])
        user_id = (last_user["user_id"] + 1) if last_user else 1000

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Create user document
        user_data = {
            "user_id": user_id,
            "username": username,
            "password": hashed_password,
            "name": name,
            "surname": surname,
            "Gender": Gender,
            "birthdate": birthdate,
            "report_count": 0,
            "created_at": datetime.now()
        }

        # Insert user into database
        users_collection.insert_one(user_data)

        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Find user
        user = users_collection.find_one({"username": username})

        if user and check_password_hash(user['password'], password):
            # Create session
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['name'] = user['name']
            session['surname'] = user['surname']
            session['birthdate'] = user['birthdate']
            session['Gender'] = user['Gender']

            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')

    if 'user_id' not in session:
        flash('Please log in to access the dashboard', 'error')
        return redirect(url_for('login'))

    # Fetch user's reports
    user_reports = list(reports_collection.find({"user_id": session['user_id']}).sort("report_number", 1))

    return render_template('index.html',
                           user=session,
                           reports=user_reports)


if __name__ == '__main__':
    app.run(debug=True)
