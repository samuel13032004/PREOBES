from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from io import BytesIO
from datetime import datetime
from recomendador.recomendador import calcular_edad


def create_pdf_report(users_collection,user_data, prediction, imc, probabilities, ai_recommendation, user_id):
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
    icon_path = "iconos/finance-and-business.png"
    img = Image(icon_path, width=20, height=20)  # Ajusta el tamaño según sea necesario

    # Cargar la imagen del icono "calendar.png"
    icon_path_calendar = "iconos/calendar.png"
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
    if isinstance(prediction, dict):
        pred_value = prediction.get("label", "")
    else:
        pred_value = prediction

    prediction_es = prediction_mapping.get(pred_value, pred_value)

    # Datos personales con icono 👤
    icon_path_user = "iconos/user.png"
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

    existing_user = users_collection.find_one({"user_id": user_id})
    # Convertir datos a formato legible para el informe
    gender = "Masculino" if existing_user["Gender"] == 'Male' else "Femenino"
    family_history = "Sí" if user_data.get('family_history') == 'yes' else "No"
    favc = "Sí" if user_data.get('FAVC') == 'yes' else "No"
    smoke = "Sí" if user_data.get('SMOKE') == 'yes' else "No"
    birthdate = existing_user["birthdate"]
    age = calcular_edad(birthdate) if birthdate else "No especificado"

    # Actividad física
    faf_mapping = {
        "0": "Sedentario",
        "1": "Ligero",
        "2": "Moderado",
        "3": "Intenso"
    }
    physical_activity = faf_mapping.get(user_data.get('FAF', '0'), "No especificado")

    user_id = existing_user["user_id"]
    report_number = existing_user["report_count"]
    print(f"ID de usuario: {user_id}")
    # Tabla de datos personales
    data = [
        ["ID Usuario", user_id],
        ["NºInforme", report_number],
        ["Nombre", existing_user["name"]],
        ["Apellidos", existing_user["surname"]],
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
    icon_path = "iconos/contract.png"
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
