import pickle


def cargar_modelos():
    with open("resultados_modelo/modelo_obesidad.pkl", "rb") as f:
        modelo_tuple = pickle.load(f)
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

    return modelo, scaler, le, model_columns
