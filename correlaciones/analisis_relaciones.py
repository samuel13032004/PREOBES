from neo4j import GraphDatabase
import pandas as pd
import scipy.stats as stats
import numpy as np
from scipy.stats import chi2_contingency
from cargar_datos.cargar_datos_neo4j import obtener_datos_completos

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "ObesityDataSet"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

def analizar_dataset(df):
    print(f"Dimensiones del dataset: {df.shape}")
    print("\nValores nulos por columna:")
    print(df.isnull().sum())

    print("\nValores únicos para variables categóricas:")
    for col in df.select_dtypes(include=['object']).columns:
        print(f"{col}: {df[col].unique()}")



def generar_reporte(correlaciones_significativas):
    correlaciones_ordenadas = sorted(
        correlaciones_significativas,
        key=lambda x: abs(x['correlation']) if x['correlation'] is not None else 0,
        reverse=True
    )

    print("\n=== REPORTE DE CORRELACIONES SIGNIFICATIVAS ===")
    print(f"Se encontraron {len(correlaciones_ordenadas)} relaciones significativas.\n")

    print("Top 10 relaciones más fuertes:")
    for i, corr in enumerate(correlaciones_ordenadas[:10], 1):
        var1, var2 = corr['vars']
        coef = corr['correlation']
        method = corr.get('method', 'desconocido')

        if method == "Pearson":
            tipo_relacion = "positiva" if coef > 0 else "negativa"
            print(f"{i}. {var1} y {var2}: Correlación {tipo_relacion} (r={coef:.3f}, p={corr['p_value']:.4f})")
        elif method == "ANOVA":
            print(f"{i}. {var1} y {var2}: Asociación por ANOVA (eta²={coef:.3f}, p={corr['p_value']:.4f})")
        else:
            print(f"{i}. {var1} y {var2}: Asociación por Chi² (V={coef:.3f}, p={corr['p_value']:.4f})")

    df_resultados = pd.DataFrame(correlaciones_ordenadas)
    df_resultados.to_csv("../PREOBES/correlaciones/correlaciones_significativas.csv", index=False)
    print("\nResultados completos guardados en 'correlaciones_significativas.csv'")


def analizar_correlacion(df, var1, var2):
    """Analiza la correlación/asociación entre dos variables"""
    if var1 not in df.columns or var2 not in df.columns:
        print(f"Error: Una de las variables {var1} o {var2} no existe en el DataFrame")
        return {"vars": [var1, var2], "correlation": None, "p_value": None, "significant": False}

    tipo_var1 = 'categórica' if df[var1].dtype == 'object' else 'numérica'
    tipo_var2 = 'categórica' if df[var2].dtype == 'object' else 'numérica'

    datos = df[[var1, var2]].dropna()

    if len(datos) < 10:
        print(f"No hay suficientes datos para analizar {var1} y {var2}")
        return {"vars": [var1, var2], "correlation": None, "p_value": None, "significant": False}

    if tipo_var1 == 'numérica' and tipo_var2 == 'numérica':
        try:
            corr, p_value = stats.pearsonr(datos[var1], datos[var2])
            print(f"Correlación de Pearson entre {var1} y {var2}: r={corr:.4f}, p={p_value:.4f}")

            return {
                "vars": [var1, var2],
                "correlation": corr,
                "p_value": p_value,
                "significant": p_value < 0.05,
                "method": "Pearson"
            }
        except Exception as e:
            print(f"Error: {e}")
            return {"vars": [var1, var2], "correlation": None, "p_value": None, "significant": False}

    elif (tipo_var1 == 'categórica' and tipo_var2 == 'numérica') or (
            tipo_var1 == 'numérica' and tipo_var2 == 'categórica'):
        try:
            cat_var = var1 if tipo_var1 == 'categórica' else var2
            num_var = var2 if tipo_var1 == 'categórica' else var1

            grupos = {}
            for categoria in datos[cat_var].unique():
                grupos[categoria] = datos[datos[cat_var] == categoria][num_var].values

            f_stat, p_value = stats.f_oneway(*grupos.values())

            n = sum(len(grupo) for grupo in grupos.values())
            k = len(grupos)
            df_between = k - 1
            df_total = n - 1
            eta_squared = (df_between * f_stat) / (df_between * f_stat + df_total)

            print(f"ANOVA para {cat_var} y {num_var}: F={f_stat:.4f}, p={p_value:.4f}, eta²={eta_squared:.4f}")

            return {
                "vars": [var1, var2],
                "correlation": eta_squared,
                "p_value": p_value,
                "significant": p_value < 0.05,
                "method": "ANOVA"
            }
        except Exception as e:
            print(f"Error: {e}")
            return {"vars": [var1, var2], "correlation": None, "p_value": None, "significant": False}

    else:
        try:
            contingency = pd.crosstab(datos[var1], datos[var2])

            chi2, p_value, dof, expected = chi2_contingency(contingency)

            n = contingency.sum().sum()
            min_dim = min(contingency.shape) - 1
            v_cramer = np.sqrt(chi2 / (n * min_dim))

            print(f"Chi-cuadrado para {var1} y {var2}: χ²={chi2:.4f}, p={p_value:.4f}, V={v_cramer:.4f}")

            return {
                "vars": [var1, var2],
                "correlation": v_cramer,
                "p_value": p_value,
                "significant": p_value < 0.05,
                "method": "Chi²"
            }
        except Exception as e:
            print(f"Error: {e}")
            return {"vars": [var1, var2], "correlation": None, "p_value": None, "significant": False}


def calcular_imc(df):
    df['Height'] = pd.to_numeric(df['Height'], errors='coerce')
    df['Weight'] = pd.to_numeric(df['Weight'], errors='coerce')

    df['IMC'] = df['Weight'] / (df['Height'] ** 2)

    bins = [0, 18.5, 25, 30, 35, 40, float('inf')]
    labels = ['Bajo peso', 'Normal', 'Sobrepeso', 'Obesidad I', 'Obesidad II', 'Obesidad III']

    df['IMC_categoria'] = pd.cut(df['IMC'], bins=bins, labels=labels)
    return df


def crear_grafo_correlaciones_neo4j_y_exportar(correlaciones_significativas, umbral=0.2,
                                               filename="../PREOBES/graficos/grafo_relaciones_neo4j.png"):

    correlaciones_filtradas = [corr for corr in correlaciones_significativas
                               if corr['correlation'] is not None and
                               abs(corr['correlation']) >= umbral]

    if not correlaciones_filtradas:
        print(f"No hay correlaciones que superen el umbral de {umbral}")
        return

    with driver.session() as session:
        session.run("""
        MATCH (v:Variable)-[r:CORRELACIONA_CON]-()
        DELETE r
        """)

        session.run("""
        MATCH (v:Variable)
        DELETE v
        """)

    variables = set()
    for corr in correlaciones_filtradas:
        variables.add(corr['vars'][0])
        variables.add(corr['vars'][1])

    with driver.session() as session:
        for var in variables:
            if var in ['IMC', 'Age', 'Height', 'Weight', 'FCVC', 'NCP', 'CH2O', 'FAF', 'TUE']:
                tipo = 'numérica'
            else:
                tipo = 'categórica'

            session.run("""
            MERGE (v:Variable {nombre: $nombre})
            SET v.tipo = $tipo
            """, nombre=var, tipo=tipo)

        for corr in correlaciones_filtradas:
            var1, var2 = corr['vars']
            correlation = corr['correlation']
            p_value = corr['p_value']
            method = corr.get('method', 'desconocido')

            direccion = None
            if method == "Pearson":
                direccion = "positiva" if correlation > 0 else "negativa"

            session.run("""
            MATCH (v1:Variable {nombre: $var1})
            MATCH (v2:Variable {nombre: $var2})
            MERGE (v1)-[r:CORRELACIONA_CON]->(v2)
            SET r.correlacion = $correlacion,
                r.p_valor = $p_valor,
                r.metodo = $metodo,
                r.fuerza = $fuerza,
                r.direccion = $direccion
            """, var1=var1, var2=var2,
                        correlacion=correlation,
                        p_valor=p_value,
                        metodo=method,
                        fuerza=abs(correlation),
                        direccion=direccion)

    print(f"Se ha creado en Neo4j un grafo con {len(variables)} variables y {len(correlaciones_filtradas)} relaciones")

    with driver.session() as session:
        result_nodes = session.run("""
        MATCH (v:Variable)
        RETURN v.nombre AS nombre, v.tipo AS tipo
        """)

        result_edges = session.run("""
        MATCH (v1:Variable)-[r:CORRELACIONA_CON]->(v2:Variable)
        RETURN v1.nombre AS origen, v2.nombre AS destino, 
               r.correlacion AS correlacion, r.metodo AS metodo,
               r.fuerza AS fuerza, r.direccion AS direccion
        """)

        nodes = [(record["nombre"], record["tipo"]) for record in result_nodes]
        edges = [(record["origen"], record["destino"],
                  record["correlacion"], record["metodo"],
                  record["fuerza"], record["direccion"])
                 for record in result_edges]

    import networkx as nx
    import matplotlib.pyplot as plt

    G = nx.Graph()

    for nombre, tipo in nodes:
        G.add_node(nombre, tipo=tipo)

    for origen, destino, correlacion, metodo, fuerza, direccion in edges:
        if metodo == "Pearson":
            color = 'green' if correlacion > 0 else 'red'
        elif metodo == "ANOVA":
            color = 'orange'
        else:  # Chi²
            color = 'purple'

        G.add_edge(origen, destino,
                   weight=fuerza,
                   correlation=correlacion,
                   metodo=metodo,
                   color=color,
                   direccion=direccion)

    plt.figure(figsize=(14, 12))

    pos = nx.spring_layout(G, seed=42, k=0.3)

    node_colors = ['skyblue' if G.nodes[node]['tipo'] == 'numérica' else 'lightgreen' for node in G.nodes()]

    edge_colors = [G[u][v]['color'] for u, v in G.edges()]

    widths = [G[u][v]['weight'] * 5 for u, v in G.edges()]

    nx.draw_networkx_nodes(G, pos, node_size=800, node_color=node_colors, alpha=0.8)
    nx.draw_networkx_edges(G, pos, width=widths, edge_color=edge_colors, alpha=0.7)
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')

    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color='green', lw=4, label='Correlación Positiva'),
        Line2D([0], [0], color='red', lw=4, label='Correlación Negativa'),
        Line2D([0], [0], color='orange', lw=4, label='ANOVA'),
        Line2D([0], [0], color='purple', lw=4, label='Chi²'),
        Line2D([0], [0], marker='o', color='w', label='Var. Numérica', markerfacecolor='skyblue', markersize=15),
        Line2D([0], [0], marker='o', color='w', label='Var. Categórica', markerfacecolor='lightgreen', markersize=15)
    ]
    plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1))

    plt.title("Grafo de relaciones significativas entre variables (desde Neo4j)", fontsize=16)
    plt.axis('off')
    plt.tight_layout()

    # Guardar como PNG
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Grafo exportado como imagen PNG: {filename}")

    return plt


def exportar_grafo_existente_a_png(correlaciones_significativas, filename="../PREOBES/graficos/grafo_relaciones_neo4j.png"):
    """
    Toma las correlaciones ya calculadas, crea el grafo en Neo4j y lo exporta como PNG
    """
    print("Creando grafo en Neo4j y exportando a PNG...")
    return crear_grafo_correlaciones_neo4j_y_exportar(correlaciones_significativas, filename=filename)

def analisis_completo_neo4j():
    print("Obteniendo datos de Neo4j...")
    df = obtener_datos_completos()

    if df.empty:
        print("Error: No se obtuvieron datos de Neo4j")
        return None

    print(f"Datos obtenidos: {len(df)} registros")

    numeric_cols = ['Age', 'Height', 'Weight', 'FCVC', 'NCP', 'CH2O', 'FAF', 'TUE']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    df = calcular_imc(df)

    analizar_dataset(df)
    variables = [col for col in df.columns if col not in ['IMC_categoria']]

    print("\n=== ANÁLISIS DE TODAS LAS COMBINACIONES DE VARIABLES ===")

    resultados_correlaciones = []

    # Para no repetir análisis, usamos combinaciones
    from itertools import combinations

    # Obtener todas las combinaciones de 2 variables
    pares_variables = list(combinations(variables, 2))
    print(f"Analizando {len(pares_variables)} pares de variables...")

    total = len(pares_variables)

    for i, (var1, var2) in enumerate(pares_variables):
        # Mostrar progreso cada 10%
        if i % (total // 10) == 0:
            print(f"Progreso: {i / total * 100:.1f}%")

        resultado = analizar_correlacion(df, var1, var2)
        resultados_correlaciones.append(resultado)

    # Filtrar correlaciones significativas (p < 0.05)
    correlaciones_significativas = [corr for corr in resultados_correlaciones
                                    if corr['significant'] and corr['correlation'] is not None]

    print(f"\nSe encontraron {len(correlaciones_significativas)} relaciones significativas entre variables.")

    print("\nCreando grafo de relaciones en Neo4j...")
    crear_grafo_correlaciones_neo4j_y_exportar(correlaciones_significativas)


    generar_reporte(correlaciones_significativas)
    exportar_grafo_existente_a_png(correlaciones_significativas)
    print("\nAnálisis completo finalizado y grafo creado en Neo4j.")
    return correlaciones_significativas


"""
if __name__ == "__main__":
    print("Iniciando análisis de relaciones entre variables...")
    correlaciones = analisis_completo_neo4j()

    # Cerrar la conexión a Neo4j
    driver.close()

    print("\nProceso completado.")
"""

