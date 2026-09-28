import pandas as pd
from pathlib import Path

import jornadas


clasificaciones = jornadas.obtener_clasificaciones_finales()


def obtener_zona(posicion):
    """
    Determina la zona de la clasificación a la que pertenece una posición.

    Zonas:

        1 - 5   -> Top 5
        6 - 10  -> 6-10
        11 - 15 -> 11-15
        16 - 20 -> 16-20
    """

    if posicion <= 5:
        return "1-5"

    if posicion <= 10:
        return "6-10"

    if posicion <= 15:
        return "11-15"

    return "16-20"


def analizar_movilidad_zonas(clasificaciones):
    """
    Analiza los movimientos de los equipos entre las cuatro zonas de la clasificación entre temporadas.

    Se calculan:

        - Equipos que permanecen en la misma zona.
        - Equipos que suben de zona.
        - Equipos que bajan de zona.
        - Movimientos entre cada par de zonas.
        - Equipos que llegan al Top 10 desde las posiciones
          11-20.
        - Equipos que llegan al Top 5 desde las posiciones
          6-20.
        - Equipos que pasan de las posiciones 1-10 a las
          posiciones 11-20.
    """

    # OBTENER LA ZONA DE CADA EQUIPO POR TEMPORADA

    temporadas = []

    for temporada in clasificaciones:

        nombre_temporada = temporada["nombre"]

        tabla = temporada["tabla_final"]

        equipos = {}

        for posicion, fila in enumerate(
            tabla.itertuples(index=False),
            start=1
        ):

            equipo = fila.Equipo

            equipos[equipo] = {
                "posicion": posicion,
                "zona": obtener_zona(posicion)
            }

        temporadas.append(
            {
                "Temporada": nombre_temporada,
                "Equipos": equipos
            }
        )

    # ANALIZAR MOVILIDAD GENERAL

    movilidad_general = []

    for i in range(1, len(temporadas)):

        temporada_anterior = temporadas[i - 1]
        temporada_actual = temporadas[i]

        misma_zona = 0
        suben = 0
        bajan = 0

        for equipo, datos_actuales in temporada_actual[
            "Equipos"
        ].items():

            if equipo not in temporada_anterior["Equipos"]:
                continue

            zona_anterior = temporada_anterior[
                "Equipos"
            ][equipo]["zona"]

            zona_actual = datos_actuales["zona"]

            orden_zonas = {
                "1-5": 1,
                "6-10": 2,
                "11-15": 3,
                "16-20": 4
            }

            if zona_actual == zona_anterior:

                misma_zona += 1

            elif (
                orden_zonas[zona_actual]
                < orden_zonas[zona_anterior]
            ):

                suben += 1

            else:

                bajan += 1

        movilidad_general.append(
            {
                "Temporada": temporada_actual["Temporada"],
                "Misma zona": misma_zona,
                "Suben de zona": suben,
                "Bajan de zona": bajan
            }
        )

    tabla_movilidad_general = pd.DataFrame(
        movilidad_general
    )

    # ANALIZAR MOVIMIENTOS ENTRE ZONAS

    movimientos = []

    zonas = [
        "1-5",
        "6-10",
        "11-15",
        "16-20"
    ]

    for i in range(1, len(temporadas)):

        temporada_anterior = temporadas[i - 1]
        temporada_actual = temporadas[i]

        conteo_movimientos = {}

        for zona_origen in zonas:

            for zona_destino in zonas:

                conteo_movimientos[
                    f"{zona_origen} -> {zona_destino}"
                ] = 0

        for equipo, datos_actuales in temporada_actual[
            "Equipos"
        ].items():

            if equipo not in temporada_anterior["Equipos"]:
                continue

            zona_anterior = temporada_anterior[
                "Equipos"
            ][equipo]["zona"]

            zona_actual = datos_actuales["zona"]

            clave = (
                f"{zona_anterior} -> {zona_actual}"
            )

            conteo_movimientos[clave] += 1

        resultado = {
            "Temporada": temporada_actual["Temporada"]
        }

        resultado.update(
            conteo_movimientos
        )

        movimientos.append(resultado)

    tabla_movimientos = pd.DataFrame(
        movimientos
    )

    # ANALIZAR MOVIMIENTOS DESTACADOS

    movimientos_destacados = []

    for i in range(1, len(temporadas)):

        temporada_anterior = temporadas[i - 1]
        temporada_actual = temporadas[i]

        llegan_top_10 = []
        llegan_top_5 = []
        bajan_11_20 = []

        for equipo, datos_actuales in temporada_actual[
            "Equipos"
        ].items():

            if equipo not in temporada_anterior["Equipos"]:
                continue

            posicion_anterior = temporada_anterior[
                "Equipos"
            ][equipo]["posicion"]

            posicion_actual = datos_actuales[
                "posicion"
            ]

            # Desde 11-20 hacia Top 10
            if (
                posicion_anterior >= 11
                and posicion_actual <= 10
            ):

                llegan_top_10.append(
                    equipo
                )

            # Desde 6-20 hacia Top 5
            if (
                posicion_anterior >= 6
                and posicion_actual <= 5
            ):

                llegan_top_5.append(
                    equipo
                )

            # Desde Top 10 hacia 11-20
            if (
                posicion_anterior <= 10
                and posicion_actual >= 11
            ):

                bajan_11_20.append(
                    equipo
                )

        movimientos_destacados.append(
            {
                "Temporada": temporada_actual["Temporada"],
                "Llegan Top 10 desde 11-20":
                    ", ".join(llegan_top_10)
                    if llegan_top_10
                    else "-",
                "Llegan Top 5 desde 6-20":
                    ", ".join(llegan_top_5)
                    if llegan_top_5
                    else "-",
                "Pasan de Top 10 a 11-20":
                    ", ".join(bajan_11_20)
                    if bajan_11_20
                    else "-"
            }
        )

    tabla_movimientos_destacados = pd.DataFrame(
        movimientos_destacados
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
        / "4 - Movilidad entre zonas de la clasificacion.xlsx"
    )

    with pd.ExcelWriter(
        ruta_resultado,
        engine="openpyxl"
    ) as escritor:

        tabla_movilidad_general.to_excel(
            escritor,
            sheet_name="Movilidad general",
            index=False
        )

        tabla_movimientos.to_excel(
            escritor,
            sheet_name="Movimientos entre zonas",
            index=False
        )

        tabla_movimientos_destacados.to_excel(
            escritor,
            sheet_name="Movimientos destacados",
            index=False
        )

    print(
        #f"\nResultado guardado en:"
        #f"\n{ruta_resultado}"
    )

    return (
        tabla_movilidad_general,
        tabla_movimientos,
        tabla_movimientos_destacados
    )



print("\n")
print(
    "ANÁLISIS 4 - MOVIMIENTO DE EQUIPOS ENTRE ZONAS DE LA TABLA EN UNA TEMPORADA "
)


(
    tabla_movilidad_general,
    tabla_movimientos,
    tabla_movimientos_destacados
) = analizar_movilidad_zonas(
    clasificaciones
)


print("LISTO!")