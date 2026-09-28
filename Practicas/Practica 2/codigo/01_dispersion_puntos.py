import pandas as pd
from pathlib import Path

import jornadas


clasificaciones = jornadas.obtener_clasificaciones_finales()



def calcular_dispersion_puntos(clasificaciones):
    """
    Calcula la dispersión y distribución de puntos de los equipos para cada temporada.

    Métricas calculadas:

        - Promedio de puntos
        - Desviación estándar
        - Mínimo
        - Máximo
        - Rango
        - Cambio de la desviación estándar respecto
          a la temporada anterior
        - Cambio del rango respecto a la temporada anterior

    """

    resultados = []

    # RECORRER CADA TEMPORADA

    for temporada in clasificaciones:

        nombre_temporada = temporada["nombre"]

        tabla = temporada["tabla_final"]

        puntos = tabla["Pts"]


        promedio = puntos.mean()

        desviacion_estandar = puntos.std()

        minimo = puntos.min()

        maximo = puntos.max()

        rango = maximo - minimo


        resultados.append(
            {
                "Temporada": nombre_temporada,
                "Promedio Pts": promedio,
                "Desv. estándar": desviacion_estandar,
                "Mínimo": minimo,
                "Máximo": maximo,
                "Rango": rango
            }
        )

    tabla_resultados = pd.DataFrame(
        resultados
    )

    tabla_resultados[
        "Cambio Desv. estándar"
    ] = (
        tabla_resultados[
            "Desv. estándar"
        ].diff()
    )

    tabla_resultados[
        "Cambio Rango"
    ] = (
        tabla_resultados[
            "Rango"
        ].diff()
    )

    tabla_resultados[
        "Promedio Pts"
    ] = tabla_resultados[
        "Promedio Pts"
    ].round(2)

    tabla_resultados[
        "Desv. estándar"
    ] = tabla_resultados[
        "Desv. estándar"
    ].round(2)

    tabla_resultados[
        "Cambio Desv. estándar"
    ] = tabla_resultados[
        "Cambio Desv. estándar"
    ].round(2)


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
        / "1 - Dispersion y distribucion de puntos.xlsx"
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
    "ANÁLISIS 1 - DISPERSIÓN Y DISTRIBUCIÓN "
    "DE PUNTOS POR TEMPORADA"
)


tabla_dispersion = calcular_dispersion_puntos(
    clasificaciones
)

print("LISTO!")


