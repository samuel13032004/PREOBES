from neo4j import GraphDatabase
import pandas as pd

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "ObesityDataSet"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))


def obtener_datos_completos():
    query = """
    MATCH (p:Persona)  
    RETURN p.genero as Gender, 
           p.edad as Age, 
           p.altura as Height, 
           p.peso as Weight, 
           p.historia_familiar as family_history,  
           p.comida_rapida as FAVC, 
           p.verduras as FCVC, 
           p.comidas_diarias as NCP,  
           p.consumo_comida_entrehoras as CAEC, 
           p.fuma as SMOKE, 
           p.agua_diaria as CH2O,  
           p.seguimiento_dieta as SCC, 
           p.actividad_fisica as FAF, 
           p.tiempo_dispositivos as TUE,  
           p.consumo_alcohol as CALC, 
           p.transporte as MTRANS, 
           p.nivel_obesidad as obesity_level
    """
    with driver.session() as session:
        result = session.run(query)
        return pd.DataFrame([dict(record) for record in result])


personas = obtener_datos_completos()
driver.close()
