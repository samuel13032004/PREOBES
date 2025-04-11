import pandas as pd
from flask import render_template, session, redirect, url_for, flash, request, jsonify
from pymongo import MongoClient


def setup_dashboard_routes(app, db_collection, users_collection, reports_collection):
    @app.route('/inicio')
    def inicio():
        if 'user_id' not in session:
            return redirect(url_for('login'))

        user = users_collection.find_one({'user_id': session['user_id']})
        return render_template('index.html', username=user['username'])

    @app.route('/dashboard')
    def dashboard():
        if 'user_id' not in session:
            flash('Please log in to access the dashboard', 'error')
            return redirect(url_for('login'))

        # Fetch user's reports
        user_reports = list(reports_collection.find({"user_id": session['user_id']}).sort("report_number", 1))

        return render_template('index.html',
                              user=session,
                              reports=user_reports)

    @app.route('/evolucion-data')
    def evolucion_data():
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

        variable_labels = {
            "imc": "Índice de Masa Corporal (IMC)",
            "prediction": "Niveles de Obesidad",
            "Weight": "Peso (kg)",
            "Height": "Altura (m)",
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

    @app.route('/api/user_reports', methods=['GET'])
    def get_user_reports():
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "No autenticado"}), 401

        import os
        reports_dir = os.path.join(app.root_path, 'static', 'reports')
        user_reports = []

        if os.path.exists(reports_dir):
            for filename in os.listdir(reports_dir):
                if f"informe_{user_id}_" in filename and filename.endswith('.pdf'):
                    try:
                        report_number = filename.split('_')[2].split('.')[0]
                        user_reports.append({
                            'filename': filename,
                            'report_number': report_number
                        })
                    except IndexError:
                        report_number = "N/A"
                        user_reports.append({
                            'filename': filename,
                            'report_number': report_number
                        })

        # Ordenar por número de informe
        try:
            user_reports.sort(key=lambda x: int(x['report_number']), reverse=True)
        except (ValueError, TypeError):
            user_reports.sort(key=lambda x: x['filename'], reverse=True)

        return jsonify({"reports": user_reports})

    @app.route("/proporciones/<variable>")
    def obtener_proporciones(variable):
        datos = list(db_collection.find({}, {"_id": 0}))
        df = pd.DataFrame(datos)

        # Convertir edad a numérico
        df['Age'] = pd.to_numeric(df['Age'], errors='coerce')
        df.dropna(subset=['Age'], inplace=True)

        # Crear grupos de edad
        bins = [14, 20, 30, 40, 50, 61]
        labels = ['14-20', '21-30', '31-40', '41-50', '51-61']
        df['Grupo_Edad'] = pd.cut(df['Age'], bins=bins, labels=labels, include_lowest=True)

        if variable not in df.columns:
            return jsonify({"error": f"La variable '{variable}' no está disponible."}), 404

        # Diccionario de traducción
        traducciones = {
            "yes": "Sí",
            "no": "No",
            "Female": "Mujer",
            "Male": "Hombre",
            "Always": "Siempre",
            "Frequently": "Frecuentemente",
            "Sometimes": "A veces",
            "Automobile": "Automóvil",
            "Motorbike": "Moto",
            "Bike" : "Bicicleta",
            "Public_Transportation": "Transporte público",
            "Walking": "Caminar",
            "Insufficient_Weight": "Peso insuficiente",
            "Normal_Weight": "Peso normal",
            "Overweight_Level_I": "Sobrepeso nivel I",
            "Overweight_Level_II": "Sobrepeso nivel II",
            "Obesity_Type_I": "Obesidad tipo I",
            "Obesity_Type_II": "Obesidad tipo II",
            "Obesity_Type_III": "Obesidad tipo III"
        }

        # Calcular proporciones
        distribucion = df.groupby(['Grupo_Edad', variable]).size().unstack().fillna(0)

        # Aplicar traducciones a las columnas
        distribucion.columns = [traducciones.get(str(col), str(col)) for col in distribucion.columns]

        proporciones = distribucion.div(distribucion.sum(axis=1), axis=0)

        # Colores para cada categoría
        colores = [
            "#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0",
            "#9966FF", "#FF9F40", "#C9CBCF", "#8AFFC1",
            "#A569BD", "#58D68D", "#F4D03F", "#DC7633"
        ]

        # Formato para Chart.js
        resultado = {
            "labels": list(proporciones.index.astype(str)),
            "datasets": [
                {
                    "label": str(col),
                    "data": list(proporciones[col]),
                    "backgroundColor": colores[i % len(colores)]
                } for i, col in enumerate(proporciones.columns)
            ]
        }

        return jsonify(resultado)
