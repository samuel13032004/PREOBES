from rutas_backend.rutas_autenticacion import setup_auth_routes
from rutas_backend.rutas_panel import setup_dashboard_routes
from rutas_backend.rutas_informe import setup_report_routes
from rutas_backend.rutas_prediccion import setup_prediction_routes


def configurar_rutas_configuracion(app, modelo, scaler, le, model_columns, db_collection,users_collection, reports_collection,
                                   token_openai):
    """
    Configura todas las rutas de la aplicación

    Args:
        app: La aplicación Flask
        modelo: El modelo de machine learning
        scaler: El escalador para los datos
        le: El label encoder
        model_columns: Las columnas usadas por el modelo
        users_collection: La colección de usuarios en la BD
        reports_collection: La colección de informes en la BD
        token_openai: El token de API para OpenAI
    """
    # Guardar la colección de informes en el config de la app para que sea accesible desde todas las rutas
    app.config['reports_collection'] = reports_collection

    # Configurar cada grupo de rutas
    setup_auth_routes(app, users_collection)
    setup_dashboard_routes(app, db_collection, users_collection, reports_collection)
    setup_report_routes(app, users_collection)
    setup_prediction_routes(app, modelo, scaler, le, model_columns, users_collection, reports_collection, token_openai)
