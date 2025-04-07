import os
import pandas as pd
from flask import request, redirect, url_for, flash, render_template, session
from datetime import datetime
from recomendador.recomendador_openai import get_ai_recommendation
from utilidades.descargar_informe import create_pdf_report


def setup_prediction_routes(app, modelo, scaler, le, model_columns, users_collection, reports_collection, token_openai):
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
            'Gender', 'Height', 'Weight', 'family_history', 'FAVC',
            'FCVC', 'NCP', 'CAEC', 'SMOKE', 'CH2O', 'SCC', 'FAF',
            'TUE', 'CALC', 'MTRANS'
        ]

        for field in required_fields:
            if field not in form_data:
                # Valores predeterminados apropiados para cada campo
                if field in ['Height', 'Weight', 'FCVC', 'NCP', 'CH2O', 'FAF', 'TUE']:
                    form_data[field] = '0'  # Valores numéricos como string
                else:
                    form_data[field] = 'no'  # Valores categóricos

        # Convertir el diccionario a DataFrame
        input_df = pd.DataFrame([form_data])

        # Convertir los campos numéricos conocidos a valores numéricos
        numeric_cols = ['Height', 'Weight', 'FCVC', 'NCP', 'CH2O', 'FAF', 'TUE']
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
        ai_recommendation = get_ai_recommendation(form_data, pred_label, imc_value, reports_collection, token_openai)

        # Guardar los datos de la sesión para la descarga del PDF
        app.config['LAST_PREDICTION'] = {
            'form_data': form_data,
            'prediction': pred_label,
            'imc': imc_value,
            'probabilities': sorted_probabilities,
            'ai_recommendation': ai_recommendation
        }

        filtered_form_data = form_data.copy()
        personal_fields = ['user_id', 'Name', 'Surname', 'birthdate', 'Gender']
        for field in personal_fields:
            if field in filtered_form_data:
                filtered_form_data.pop(field)

        # Guardar en la BD el informe del usuario
        report_entry = {
            "user_id": user_id,
            "report_number": report_number,
            "date": datetime.now(),
            "imc": imc_value,
            "prediction": pred_label,
            "probabilities": {le.inverse_transform([i])[0]: round(prob * 100, 2) for i, prob in enumerate(pred_proba)},
            "form_data": filtered_form_data
        }
        reports_collection.insert_one(report_entry)

        pdf_buffer = create_pdf_report(
            users_collection,
            form_data,
            pred_label,
            imc_value,
            sorted_probabilities,
            ai_recommendation,
            user_id
        )

        # Crear carpeta si no existe
        output_dir = "static/reports"
        os.makedirs(output_dir, exist_ok=True)

        # Nombre personalizado
        filename = f"informe_{user_id}_{report_number}.pdf"
        file_path = os.path.join(output_dir, filename)

        # Guardar PDF en disco
        with open(file_path, "wb") as f:
            f.write(pdf_buffer.getbuffer())

        return render_template(
            'result.html',
            prediction=pred_label,
            imc=imc_value,
            probabilities=sorted_probabilities,
            ai_recommendation=ai_recommendation
        )
