from flask import session, send_file
from utilidades.descargar_informe import create_pdf_report


def setup_report_routes(app, users_collection):
    @app.route('/download-report')
    def download_report():
        """
        Genera y descarga un informe PDF con los resultados de la evaluación
        """
        user_id = session.get('user_id')
        if not user_id:
            return "Debes iniciar sesión para descargar el informe.", 401

        last_report = app.config.get('reports_collection').find_one(
            {"user_id": user_id},
            sort=[("report_number", -1)]
        )

        if not last_report:
            return "No hay informes disponibles para este usuario.", 400

        report_number = last_report.get("report_number", "desconocido")

        last_prediction = app.config.get('LAST_PREDICTION')

        if not last_prediction:
            return "No hay datos disponibles para generar el informe. Por favor, realice una evaluación primero.", 400

        pdf_buffer = create_pdf_report(
            users_collection,
            last_prediction['form_data'],
            last_prediction['prediction'],
            last_prediction['imc'],
            last_prediction['probabilities'],
            last_prediction['ai_recommendation'],
            user_id
        )

        filename = f"informe_{user_id}_{report_number}.pdf"

        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
