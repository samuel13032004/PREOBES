from flask import render_template, request, redirect, url_for, session, flash, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
from datetime import datetime
from recomendador.recomendador import get_ai_recommendation
from utilidades.descargar_informe import create_pdf_report


def configurar_rutas_configuracion(app, modelo, scaler, le, model_columns, users_collection, reports_collection,
                                   token_openai):
    @app.route('/')
    def index():
        return render_template('login.html')


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


    @app.route('/evolucion-data')
    def evolucion_data():
        user_id = request.args.get("user_id", type=int)

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
            users_collection,
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
        ai_recommendation = get_ai_recommendation(form_data, pred_label, imc_value,token_openai)

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
