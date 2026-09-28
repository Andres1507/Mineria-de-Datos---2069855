from pathlib import Path
import pandas as pd

from jornadas import obtener_clasificaciones_finales


def analizar_momento_definicion_campeonato():

    ruta_dataset = (
        Path(__file__).resolve().parents[2]
        / "Dataset"
        / "Dataset Limpio"
        / "dataset_limpio_definitivo.xlsx"
    )

    carpeta_resultados = (
        Path(__file__).resolve().parents[1]
        / "doc"
        / "resultados"
    )

    carpeta_resultados.mkdir(parents=True, exist_ok=True)

    ruta_salida = (
        carpeta_resultados
        / "8 - Momento de Definicion del Campeonato.xlsx"
    )

    df = pd.read_excel(ruta_dataset)

    if len(df) != 5700:
        raise ValueError(
            f"Se esperaban 5700 partidos, pero se encontraron {len(df)}."
        )

    temporadas = []

    for inicio in range(0, len(df), 380):
        fecha = pd.to_datetime(df.iloc[inicio]["Date"])

        año_inicio = fecha.year

        temporada = (
            f"{año_inicio}-{str(año_inicio + 1)[-2:]}"
        )

        temporadas.extend([temporada] * 380)

    df["Temporada"] = temporadas


    clasificaciones = obtener_clasificaciones_finales()

    campeones = {}

    for temporada in clasificaciones:
        tabla = temporada["tabla_final"]

        campeon = tabla.iloc[0]["Equipo"]

        campeones[temporada["nombre"]] = campeon


    resultados = []


    for nombre_temporada, campeon in campeones.items():

        partidos = df[
            df["Temporada"] == nombre_temporada
        ].copy()


        partidos["Fecha"] = pd.to_datetime(
            partidos["Date"]
        )

        partidos["Hora"] = pd.to_datetime(
            partidos["Time"],
            format="%H:%M",
            errors="coerce"
        ).dt.time

        # Crear una columna auxiliar para ordenar
        partidos["FechaHora"] = pd.to_datetime(
            partidos["Date"].astype(str)
            + " "
            + partidos["Time"].astype(str),
            errors="coerce"
        )

        partidos = partidos.sort_values(
            ["FechaHora"]
        ).reset_index(drop=True)


        equipos = sorted(
            set(partidos["HomeTeam"])
            | set(partidos["AwayTeam"])
        )

        # Estado inicial de la temporada

        puntos = {
            equipo: 0
            for equipo in equipos
        }

        partidos_jugados = {
            equipo: 0
            for equipo in equipos
        }

        definicion_encontrada = False


        for _, partido in partidos.iterrows():

            local = partido["HomeTeam"]
            visitante = partido["AwayTeam"]

            # Actualizar puntos

            if partido["FTR"] == "H":

                puntos[local] += 3

            elif partido["FTR"] == "A":

                puntos[visitante] += 3

            elif partido["FTR"] == "D":

                puntos[local] += 1
                puntos[visitante] += 1

            # Actualizar partidos jugados

            partidos_jugados[local] += 1
            partidos_jugados[visitante] += 1

            # Si todavía no se ha definido el campeonato, comprobar si el campeón ya es inalcanzable.

            if not definicion_encontrada:

                puntos_campeon = puntos[campeon]

                maximos_rivales = {}

                for equipo in equipos:

                    if equipo == campeon:
                        continue

                    partidos_restantes = (
                        38 - partidos_jugados[equipo]
                    )

                    maximo_puntos = (
                        puntos[equipo]
                        + partidos_restantes * 3
                    )

                    maximos_rivales[equipo] = maximo_puntos

                # Encontrar al rival con mayor cantidad de puntos que todavía podría alcanzar.

                rival_maximo = max(
                    maximos_rivales,
                    key=maximos_rivales.get
                )

                maximo_rival = maximos_rivales[
                    rival_maximo
                ]

                # El campeonato queda definido cuando ningún rival puede alcanzar los puntos actuales del campeón actual
                if maximo_rival < puntos_campeon:

                    fecha_definicion = partido["Fecha"]

                    resultados.append({
                        "Temporada": nombre_temporada,
                        "Campeón": campeon,
                        "Fecha de definición": fecha_definicion,
                        "Partido de definición": (
                            f"{local} vs {visitante}"
                        ),
                        "Partidos disputados por el campeón":
                            partidos_jugados[campeon],
                        "Puntos del campeón":
                            puntos_campeon,
                        "Rival con mayor máximo posible":
                            rival_maximo,
                        "Máximo de puntos posible del rival":
                            maximo_rival,
                        "Diferencia mínima de puntos":
                            puntos_campeon - maximo_rival
                    })

                    definicion_encontrada = True


        if not definicion_encontrada:

            resultados.append({
                "Temporada": nombre_temporada,
                "Campeón": campeon,
                "Fecha de definición": "No encontrada",
                "Partido de definición": "No encontrada",
                "Partidos disputados por el campeón":
                    partidos_jugados[campeon],
                "Puntos del campeón":
                    puntos[campeon],
                "Rival con mayor máximo posible":
                    "N/A",
                "Máximo de puntos posible del rival":
                    "N/A",
                "Diferencia mínima de puntos":
                    "N/A"
            })

    resultados_df = pd.DataFrame(resultados)


    resultados_df = resultados_df.sort_values(
        "Temporada"
    ).reset_index(drop=True)


    with pd.ExcelWriter(
        ruta_salida,
        engine="openpyxl"
    ) as writer:

        resultados_df.to_excel(
            writer,
            sheet_name="Definición campeonato",
            index=False
        )




print("\n")
print(
    "ANÁLISIS 8 - DEFINICION DEL CAMPEONATO  "
)


analizar_momento_definicion_campeonato()


print("LISTO!")