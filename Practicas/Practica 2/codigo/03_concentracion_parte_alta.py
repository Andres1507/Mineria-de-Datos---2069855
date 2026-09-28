import pandas as pd
from pathlib import Path

import jornadas


clasificaciones = jornadas.obtener_clasificaciones_finales()



def analizar_concentracion_parte_alta(clasificaciones):
    """
    Analiza la presencia y permanencia de los equipo dentro del Top 5 de cada temporada.

    Se calculan:

        - Número de apariciones de cada equipo en el Top 5.
        - Porcentaje de temporadas en Top 5.
        - Equipos que permanecen en el Top 5 entre temporadas.
        - Equipos nuevos que entran al Top 5.
        - Equipos que salen del Top 5.
        - Racha máxima de temporadas consecutivas
          dentro del Top 5.
    """

    # OBTENER TOP 5 DE CADA TEMPORADA

    tops_5 = []

    for temporada in clasificaciones:

        nombre_temporada = temporada["nombre"]

        tabla = temporada["tabla_final"]

        top_5 = tabla.head(5)["Equipo"].tolist()

        tops_5.append(
            {
                "Temporada": nombre_temporada,
                "Equipos": top_5
            }
        )

    # CONTAR APARICIONES EN TOP 5

    apariciones = {}

    for temporada in tops_5:

        for equipo in temporada["Equipos"]:

            if equipo not in apariciones:
                apariciones[equipo] = 0

            apariciones[equipo] += 1

    tabla_apariciones = pd.DataFrame(
        [
            {
                "Equipo": equipo,
                "Apariciones Top 5": cantidad,
                "% de temporadas": (
                    cantidad / len(clasificaciones)
                ) * 100
            }
            for equipo, cantidad in apariciones.items()
        ]
    )

    tabla_apariciones = tabla_apariciones.sort_values(
        by="Apariciones Top 5",
        ascending=False
    )

    tabla_apariciones[
        "% de temporadas"
    ] = tabla_apariciones[
        "% de temporadas"
    ].round(2)

    # ANALIZAR CONTINUIDAD ENTRE TEMPORADAS

    continuidad = []

    for i in range(1, len(tops_5)):

        temporada_anterior = tops_5[i - 1]

        temporada_actual = tops_5[i]

        equipos_anteriores = set(
            temporada_anterior["Equipos"]
        )

        equipos_actuales = set(
            temporada_actual["Equipos"]
        )

        permanecen = (
            equipos_anteriores
            & equipos_actuales
        )

        nuevos = (
            equipos_actuales
            - equipos_anteriores
        )

        salen = (
            equipos_anteriores
            - equipos_actuales
        )

        continuidad.append(
            {
                "Temporada": temporada_actual["Temporada"],
                "Permanecen Top 5": len(permanecen),
                "Equipos nuevos": len(nuevos),
                "Equipos que salen": len(salen)
            }
        )

    tabla_continuidad = pd.DataFrame(
        continuidad
    )

    # CALCULAR RACHAS MÁXIMAS DE CADA EQUIPO
    equipos = set()

    for temporada in tops_5:

        equipos.update(
            temporada["Equipos"]
        )

    rachas = []

    for equipo in equipos:

        racha_actual = 0

        racha_maxima = 0

        for temporada in tops_5:

            if equipo in temporada["Equipos"]:

                racha_actual += 1

                if racha_actual > racha_maxima:

                    racha_maxima = racha_actual

            else:

                racha_actual = 0

        rachas.append(
            {
                "Equipo": equipo,
                "Racha máxima Top 5": racha_maxima
            }
        )

    tabla_rachas = pd.DataFrame(
        rachas
    )

    tabla_rachas = tabla_rachas.sort_values(
        by="Racha máxima Top 5",
        ascending=False
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
        / "3 - Concentracion y estabilidad parte alta.xlsx"
    )

    with pd.ExcelWriter(
        ruta_resultado,
        engine="openpyxl"
    ) as escritor:

        tabla_apariciones.to_excel(
            escritor,
            sheet_name="Apariciones Top 5",
            index=False
        )

        tabla_continuidad.to_excel(
            escritor,
            sheet_name="Continuidad Top 5",
            index=False
        )

        tabla_rachas.to_excel(
            escritor,
            sheet_name="Rachas Top 5",
            index=False
        )


    print(
        #f"\nResultado guardado en:"
        #f"\n{ruta_resultado}"
    )

    return (
        tabla_apariciones,
        tabla_continuidad,
        tabla_rachas
    )


print("\n")
print(
    "ANÁLISIS 3 - PRESENCIA Y PERMANENCIA EN LA PARTE ALTA DE LA TABLA ")

(
    tabla_apariciones,
    tabla_continuidad,
    tabla_rachas
) = analizar_concentracion_parte_alta(
    clasificaciones
)

print("LISTO!")
