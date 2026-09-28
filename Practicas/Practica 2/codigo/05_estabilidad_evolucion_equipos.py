import pandas as pd
from pathlib import Path

import jornadas

clasificaciones = jornadas.obtener_clasificaciones_finales()


def analizar_estabilidad_equipos(clasificaciones):
    """
    Analiza el comportamiento de cada equipo a través de las temporadas en las que participó.

    Se calculan:

        - Temporadas participadas.
        - Mejor posición.
        - Peor posición.
        - Posición promedio.
        - Desviación estándar de la posición.
        - Rango de posiciones.
        - Mejor temporada.
        - Peor temporada.
        - Puntos por temporada.
        - Goles a favor.
        - Goles en contra.
        - Cambio de posición respecto a la temporada anterior.
    """

    # CONSTRUIR HISTORIAL DE CADA EQUIPO

    historial = []

    for temporada in clasificaciones:

        nombre_temporada = temporada["nombre"]

        tabla = temporada["tabla_final"]

        for posicion, fila in enumerate(
            tabla.itertuples(index=False),
            start=1
        ):

            historial.append(
                {
                    "Temporada": nombre_temporada,
                    "Equipo": fila.Equipo,
                    "Posición": posicion,
                    "Puntos": fila.Pts,
                    "Goles a favor": fila.GF,
                    "Goles en contra": fila.GC
                }
            )

    tabla_historial = pd.DataFrame(
        historial
    )


    tabla_historial = tabla_historial.sort_values(
        by=[
            "Equipo",
            "Temporada"
        ]
    ).reset_index(drop=True)

    tabla_historial[
        "Posición anterior"
    ] = (
        tabla_historial
        .groupby("Equipo")["Posición"]
        .shift(1)
    )

    tabla_historial[
        "Cambio de posición"
    ] = (
        tabla_historial[
            "Posición anterior"
        ]
        - tabla_historial[
            "Posición"
        ]
    )

    resumen = []

    for equipo, grupo in tabla_historial.groupby(
        "Equipo"
    ):

        grupo = grupo.sort_values(
            by="Temporada"
        )

        mejor_posicion = grupo[
            "Posición"
        ].min()

        peor_posicion = grupo[
            "Posición"
        ].max()

        posicion_promedio = grupo[
            "Posición"
        ].mean()

        desviacion_posicion = grupo[
            "Posición"
        ].std()

        rango_posicion = (
            peor_posicion
            - mejor_posicion
        )

        mejor_fila = grupo.loc[
            grupo["Posición"].idxmin()
        ]

        peor_fila = grupo.loc[
            grupo["Posición"].idxmax()
        ]

        resumen.append(
            {
                "Equipo": equipo,
                "Temporadas participadas": len(grupo),
                "Mejor posición": mejor_posicion,
                "Peor posición": peor_posicion,
                "Posición promedio": posicion_promedio,
                "Desv. estándar posición":
                    desviacion_posicion,
                "Rango de posiciones":
                    rango_posicion,
                "Mejor temporada":
                    mejor_fila["Temporada"],
                "Peor temporada":
                    peor_fila["Temporada"]
            }
        )

    tabla_resumen = pd.DataFrame(
        resumen
    )


    tabla_resumen[
        "Posición promedio"
    ] = tabla_resumen[
        "Posición promedio"
    ].round(2)

    tabla_resumen[
        "Desv. estándar posición"
    ] = tabla_resumen[
        "Desv. estándar posición"
    ].round(2)


    tabla_resumen = tabla_resumen.sort_values(
        by=[
            "Posición promedio",
            "Equipo"
        ]
    ).reset_index(drop=True)


    tabla_evolucion = tabla_historial[
        [
            "Temporada",
            "Equipo",
            "Posición",
            "Puntos",
            "Goles a favor",
            "Goles en contra"
        ]
    ].copy()

    tabla_evolucion = tabla_evolucion.sort_values(
        by=[
            "Equipo",
            "Temporada"
        ]
    ).reset_index(drop=True)


    tabla_cambios = tabla_historial[
        [
            "Temporada",
            "Equipo",
            "Posición anterior",
            "Posición",
            "Cambio de posición"
        ]
    ].copy()

    tabla_cambios = tabla_cambios.dropna(
        subset=[
            "Posición anterior"
        ]
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
        / "5 - Estabilidad y evolucion individual de los equipos.xlsx"
    )

    with pd.ExcelWriter(
        ruta_resultado,
        engine="openpyxl"
    ) as escritor:

        tabla_resumen.to_excel(
            escritor,
            sheet_name="Resumen por equipo",
            index=False
        )

        tabla_evolucion.to_excel(
            escritor,
            sheet_name="Evolución por temporada",
            index=False
        )

        tabla_cambios.to_excel(
            escritor,
            sheet_name="Cambios de posición",
            index=False
        )


    print(
        #f"\nResultado guardado en:"
        #f"\n{ruta_resultado}"
    )

    return (
        tabla_resumen,
        tabla_evolucion,
        tabla_cambios
    )





print("\n")
print(
    "ANÁLISIS 5 - COMPORTAMIENTO / EVOLUCION DE LOS EQUIPOS POR TEMPORADA "
)

(
    tabla_resumen,
    tabla_evolucion,
    tabla_cambios
) = analizar_estabilidad_equipos(
    clasificaciones
)


print("LISTO!")