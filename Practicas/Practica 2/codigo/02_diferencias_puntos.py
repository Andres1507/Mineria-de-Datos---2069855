import pandas as pd
from pathlib import Path

import jornadas


clasificaciones = jornadas.obtener_clasificaciones_finales()


def calcular_diferencias_puntos_posicion(clasificaciones):
    """
    Calcula las diferencias de puntos entre posiciones específicas de la clasificación final de cada temporada.

    Comparaciones realizadas:

        - 1.º - 2.º (para calcular las diferencias puntuales entre campeon y subcampeon)
        - 5.º - 6.º (son aquellos equipos que para esta liga, clasifican a competencias europeas, vale la pena ver su desempeño)
        - 10.º - 11.º (son los equipos que comunmente se les conoce como de 'media tabla' y es interesante compararlos con los demas)
        - 19.º - 20.º (los dos peores equipos de la temporada, son los que descienden a segunda al finalizar el toerneo )

    """

    resultados = []


    for temporada in clasificaciones:

        nombre_temporada = temporada["nombre"]

        tabla = temporada["tabla_final"]


        puntos_1 = tabla.iloc[0]["Pts"]
        puntos_2 = tabla.iloc[1]["Pts"]

        puntos_5 = tabla.iloc[4]["Pts"]
        puntos_6 = tabla.iloc[5]["Pts"]

        puntos_10 = tabla.iloc[9]["Pts"]
        puntos_11 = tabla.iloc[10]["Pts"]

        puntos_19 = tabla.iloc[18]["Pts"]
        puntos_20 = tabla.iloc[19]["Pts"]


        diferencia_1_2 = puntos_1 - puntos_2

        diferencia_5_6 = puntos_5 - puntos_6

        diferencia_10_11 = puntos_10 - puntos_11

        diferencia_19_20 = puntos_19 - puntos_20


        resultados.append(
            {
                "Temporada": nombre_temporada,
                "1.º - 2.º": diferencia_1_2,
                "5.º - 6.º": diferencia_5_6,
                "10.º - 11.º": diferencia_10_11,
                "19.º - 20.º": diferencia_19_20
            }
        )


    tabla_resultados = pd.DataFrame(
        resultados
    )

    carpeta_resultados = (
        Path(__file__).resolve().parents[1]
        / "doc"
        / "resultados"
    )

    carpeta_resultados.mkdir(
        parents=True,
        exist_ok=True
    )

    ruta_resultado = (
        carpeta_resultados
        / "2 - Diferencias de puntos por posicion.xlsx"
    )

    tabla_resultados.to_excel(
        ruta_resultado,
        index=False
    )


    print(
        #f"\nResultado guardado en:"
        #f"\n{ruta_resultado}"
    )

    return tabla_resultados



print("\n")
print(
    "ANÁLISIS 2 - DIFERENCIAS DE PUNTOS  "
)


tabla_diferencias = calcular_diferencias_puntos_posicion(
    clasificaciones
)

print("LISTO!")
