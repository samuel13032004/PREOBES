from neo4j import GraphDatabase
import pandas as pd

# Configuración de la conexión
URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "ObesityDataSet"

# Conectar a Neo4j
driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

def obtener_personas():
    query = """
    MATCH (p:Persona) 
    RETURN p.genero, p.edad, p.altura, p.peso, p.historia_familiar, 
           p.comida_rapida, p.verduras, p.comidas_diarias, 
           p.consumo_comida_entrehoras, p.fuma, p.agua_diaria, 
           p.seguimiento_dieta, p.actividad_fisica, p.tiempo_dispositivos, 
           p.consumo_alcohol, p.transporte, p.nivel_obesidad
    LIMIT 10
    """
    with driver.session() as session:
        result = session.run(query)
        return [record for record in result]

# 📌 Obtener datos y mostrarlos
personas = obtener_personas()
for persona in personas:
    print(persona)


def obtener_datos():
    query = """
    MATCH (p:Persona) 
    RETURN p.actividad_fisica AS actividad_fisica, 
           p.tiempo_dispositivos AS tiempo_dispositivos,
           p.consumo_alcohol AS consumo_alcohol,
           p.nivel_obesidad AS nivel_obesidad
    """
    with driver.session() as session:
        result = session.run(query)
        return pd.DataFrame([dict(record) for record in result])

# 📌 Convertir datos a DataFrame
df = obtener_datos()

df["consumo_alcohol"] = df["consumo_alcohol"].astype("category").cat.codes
df["nivel_obesidad"] = df["nivel_obesidad"].astype("category").cat.codes

# 📌 Mostrar matriz de correlación
print(df.corr())

# 📌 Cerrar conexión
driver.close()
