import pandas as pd
from pathlib import Path

import jornadas


def calcular_cambios_entre_etapas(tabla_evolucion):
    """
    Calcula los cambios de posición entre cada una de las 38 clasificaciones progresivas.
    Cada fila representa a un equipo pasando de una etapa a la siguiente: 1->2, 2->3, ..., 37->38.
    """
    datos = tabla_evolucion.copy()

    datos = datos.sort_values(by=["Temporada", "Equipo", "Partidos disputados"]).reset_index(drop=True)

    datos["Posición anterior"] = (datos.groupby(["Temporada", "Equipo"])["Posición"].shift(1))

    datos = datos[datos["Posición anterior"].notna()].copy()

    datos["Etapa anterior"] = (datos["Partidos disputados"] - 1)

    datos["Cambio de posición"] = (datos["Posición anterior"] - datos["Posición"])

    datos["Cambio absoluto"] = (datos["Cambio de posición"].abs())

    datos["Mantuvo posición"] = (datos["Cambio de posición"] == 0)

    datos["Mejoró posición"] = (datos["Cambio de posición"] > 0)

    datos["Empeoró posición"] = (datos["Cambio de posición"] < 0)

    datos["Etapa"] = datos["Partidos disputados"].apply(
        lambda x: "Primera mitad" if x <= 19 else "Segunda mitad"
    )

    return datos[
        [
            "Temporada",
            "Etapa anterior",
            "Partidos disputados",
            "Equipo",
            "Posición anterior",
            "Posición",
            "Cambio de posición",
            "Cambio absoluto",
            "Mantuvo posición",
            "Mejoró posición",
            "Empeoró posición",
            "Etapa"
        ]
    ]


def calcular_inicio_mitad_final(tabla_evolucion):
    """
    Compara la posición de cada equipo después de su partido 1,
    después del partido 19 y al finalizar la temporada.
    """

    puntos_referencia = tabla_evolucion[tabla_evolucion["Partidos disputados"].isin([1, 19, 38])].copy()

    posiciones = puntos_referencia.pivot_table(
        index=["Temporada", "Equipo"],
        columns="Partidos disputados",
        values="Posición",
        aggfunc="first"
    ).reset_index()

    posiciones = posiciones.rename(columns={
            1: "Posición inicial",
            19: "Posición a mitad de temporada",
            38: "Posición final"})

    # CAMBIOS ENTRE LOS TRES PUNTOS DE REFERENCIA
    posiciones["Cambio inicial a mitad"] = (posiciones["Posición inicial"] - posiciones["Posición a mitad de temporada"])

    posiciones["Cambio mitad a final"] = (posiciones["Posición a mitad de temporada"] - posiciones["Posición final"])

    posiciones["Cambio inicial a final"] = (posiciones["Posición inicial"] - posiciones["Posición final"])

    posiciones["Cambio absoluto inicial a mitad"] = (posiciones["Cambio inicial a mitad"].abs())

    posiciones["Cambio absoluto mitad a final"] = (posiciones["Cambio mitad a final"].abs())

    posiciones["Cambio absoluto inicial a final"] = (posiciones["Cambio inicial a final"].abs())

    return posiciones.sort_values(by=["Temporada", "Posición final", "Equipo"]).reset_index(drop=True)


def calcular_resumen_por_temporada(
    tabla_evolucion,
    cambios_etapas,
    inicio_mitad_final
):
    """
    Genera un resumen de cómo cambia y se estabiliza la clasificación durante cada temporada.
    Se utilizan las 38 tablas progresivas mediante los cambio entre cada etapa consecutiva.
    """

    resumen = []

    for temporada, grupo in cambios_etapas.groupby("Temporada", sort=False):

        primera_mitad = grupo[grupo["Partidos disputados"] <= 19]

        segunda_mitad = grupo[grupo["Partidos disputados"] >= 20]

        # CAMBIO PROMEDIO POR ETAPA
        cambio_promedio_total = grupo["Cambio absoluto"].mean()
        cambio_promedio_primera = primera_mitad["Cambio absoluto"].mean()
        cambio_promedio_segunda = segunda_mitad["Cambio absoluto"].mean()

        # EQUIPOS QUE MANTIENEN POSICIÓN ENTRE ETAPAS
        porcentaje_mantienen_total = (grupo["Mantuvo posición"].mean() * 100)

        porcentaje_mantienen_primera = (primera_mitad["Mantuvo posición"].mean() * 100)

        porcentaje_mantienen_segunda = (segunda_mitad["Mantuvo posición"].mean() * 100)

        # CAMBIOS DE LIDERAZGO EN LA TABLA
        tablas_temporada = tabla_evolucion[tabla_evolucion["Temporada"] == temporada].copy()

        lideres = (
            tablas_temporada[
                tablas_temporada["Posición"] == 1
            ]
            .sort_values("Partidos disputados")
        )

        lideres = lideres.drop_duplicates(
            subset=["Partidos disputados"]
        )

        lideres_anteriores = lideres["Equipo"].shift(1)
        cambios_lider = int(
            (lideres["Equipo"] != lideres_anteriores)
            .iloc[1:]
            .sum()
        )

        # ÚLTIMA ETAPA EN LA QUE CAMBIÓ EL LÍDER
        etapas_cambio_lider = lideres.loc[
            lideres["Equipo"] != lideres["Equipo"].shift(1),
            "Partidos disputados"
        ].iloc[1:]

        if len(etapas_cambio_lider) > 0:
            ultima_etapa_cambio_lider = int(
                etapas_cambio_lider.max()
            )
        else:
            ultima_etapa_cambio_lider = 0

        # MOVIMIENTO MÁXIMO ENTRE DOS ETAPAS
        mayor_ascenso = int(grupo["Cambio de posición"].max())

        mayor_descenso = int(grupo["Cambio de posición"].min())

        mayor_movimiento = int( grupo["Cambio absoluto"].max())


        # TOP 5: CUÁNTOS SE MANTIENEN ENTRE ETAPAS
        retenciones_top5 = []

        for etapa in range(2, 39):

            anterior = tablas_temporada[tablas_temporada["Partidos disputados"] == etapa - 1]

            actual = tablas_temporada[tablas_temporada["Partidos disputados"] == etapa]

            top5_anterior = set(
                anterior.loc[
                    anterior["Posición"] <= 5,
                    "Equipo"
                ]
            )

            top5_actual = set(
                actual.loc[
                    actual["Posición"] <= 5,
                    "Equipo"
                ]
            )

            retenciones_top5.append(len(top5_anterior & top5_actual))

        retenciones_top5 = pd.Series(retenciones_top5)

        # TOP 5 INICIAL, MITAD Y FINAL
        puntos = inicio_mitad_final[inicio_mitad_final["Temporada"] == temporada]

        top5_inicial = set(
            puntos.loc[
                puntos["Posición inicial"] <= 5,
                "Equipo"
            ]
        )

        top5_mitad = set(
            puntos.loc[
                puntos["Posición a mitad de temporada"] <= 5,
                "Equipo"
            ]
        )

        top5_final = set(
            puntos.loc[
                puntos["Posición final"] <= 5,
                "Equipo"
            ]
        )

        resumen.append({
            "Temporada": temporada,

            "Cambio promedio por etapa": round(
                cambio_promedio_total, 2
            ),

            "Cambio promedio por etapa 1-19": round(
                cambio_promedio_primera, 2),

            "Cambio promedio por etapa 20-38": round(
                cambio_promedio_segunda, 2),

            "% de posiciones que se mantienen": round(
                porcentaje_mantienen_total, 2),

            "% de posiciones que se mantienen 1-19": round(
                porcentaje_mantienen_primera, 2),

            "% de posiciones que se mantienen 20-38": round(
                porcentaje_mantienen_segunda, 2),

            "Cambios de líder": cambios_lider,

            "Último cambio de líder en partido": (
                ultima_etapa_cambio_lider),

            "Mayor ascenso entre etapas": mayor_ascenso,

            "Mayor descenso entre etapas": mayor_descenso,

            "Mayor movimiento entre etapas": mayor_movimiento,

            "Top 5 promedio que se mantiene entre etapas": round(
                retenciones_top5.mean(), 2),

            "Top 5 inicial que permanece a mitad": len(
                top5_inicial & top5_mitad),

            "Top 5 mitad que permanece al final": len(
                top5_mitad & top5_final),

            "Top 5 inicial que permanece al final": len(
                top5_inicial & top5_final)
        })

    return pd.DataFrame(resumen)


def analizar_evolucion_clasificacion():
    """
    Analiza cómo se va formando y estabilizando la clasificación durante las 15 temporadas del dataset.

    Para cada temporada se generan 38 tablas progresivas.
    Cada tabla representa la clasificación después de que cada
    equipo haya disputado N partidos en orden cronológico.

    El análisis aprovecha las 38 tablas para estudiar:

        - Los cambios entre etapas consecutivas.
        - La estabilidad de las posiciones durante la primera y
          segunda mitad de la temporada.
        - Los cambios de liderazgo.
        - La permanencia del Top 5 durante la temporada.
        - La comparación entre inicio, mitad y final.
        - Los movimientos extremos entre posiciones consecutivas.

    Importante:

        Las 38 tablas representan los primeros N partidos
        disputados por cada equipo en orden cronológico.
        Por lo tanto, no necesariamente corresponden a las
        jornadas oficiales cuando existen partidos aplazados.
    """

    ruta_dataset = (
        Path(__file__).resolve().parents[2]
        / "Dataset"
        / "Dataset Limpio"
        / "dataset_limpio_definitivo.xlsx"
    )

    if not ruta_dataset.exists():
        ruta_dataset = Path(__file__).resolve().parent / "dataset_limpio_definitivo.xlsx"

    if not ruta_dataset.exists():
        raise FileNotFoundError(
            "No se encontró el dataset_limpio_definitivo.xlsx. "
            "Verifica la ruta del proyecto."
        )

    df = pd.read_excel(ruta_dataset)

    if len(df) != 5700:
        raise ValueError(
            f"Se esperaban 5700 partidos, pero se encontraron {len(df)}."
        )

    partidos_por_temporada = 380

    if len(df) % partidos_por_temporada != 0:
        raise ValueError(
            "El dataset no contiene una cantidad de partidos divisible entre 380."
        )

    cantidad_temporadas = len(df) // partidos_por_temporada


    evolucion_progresiva = []


    for numero_temporada in range(cantidad_temporadas):

        inicio = numero_temporada * partidos_por_temporada
        fin = inicio + partidos_por_temporada

        df_temporada = df.iloc[inicio:fin].copy()


        fecha_inicio = pd.to_datetime(
            df_temporada.iloc[0]["Date"]
        )

        fecha_fin = pd.to_datetime(
            df_temporada.iloc[-1]["Date"]
        )

        nombre_temporada = (
            f"{fecha_inicio.year}-"
            f"{str(fecha_fin.year)[-2:]}"
        )

        equipos_locales = df_temporada["HomeTeam"].unique()
        equipos_visitantes = df_temporada["AwayTeam"].unique()

        equipos = sorted(
            set(equipos_locales) | set(equipos_visitantes)
        )

        if len(equipos) != 20:
            raise ValueError(
                f"La temporada {nombre_temporada} no contiene 20 equipos."
            )

        partidos_por_equipo = {}

        for equipo in equipos:

            partidos_local = df_temporada[
                df_temporada["HomeTeam"] == equipo
            ].copy()

            partidos_visitante = df_temporada[
                df_temporada["AwayTeam"] == equipo
            ].copy()

            partidos_equipo = pd.concat(
                [partidos_local, partidos_visitante]
            )

            partidos_equipo = partidos_equipo.sort_values(
                by=["Date", "Time"]
            )

            if len(partidos_equipo) != 38:
                raise ValueError(
                    f"El equipo {equipo} de {nombre_temporada} "
                    f"no tiene 38 partidos."
                )

            partidos_por_equipo[equipo] = partidos_equipo


        for numero_partido in range(1, 39):

            datos_tabla = []

            for equipo in equipos:

                partidos_equipo = partidos_por_equipo[equipo]

                primeros_partidos = partidos_equipo.iloc[:numero_partido]

                puntos = 0
                victorias = 0
                empates = 0
                derrotas = 0
                goles_favor = 0
                goles_contra = 0

                for _, partido in primeros_partidos.iterrows():

                    if partido["HomeTeam"] == equipo:
                        goles_equipo = partido["FTHG"]
                        goles_rival = partido["FTAG"]
                    else:
                        goles_equipo = partido["FTAG"]
                        goles_rival = partido["FTHG"]

                    goles_favor += goles_equipo
                    goles_contra += goles_rival

                    if goles_equipo > goles_rival:
                        victorias += 1
                        puntos += 3

                    elif goles_equipo == goles_rival:
                        empates += 1
                        puntos += 1

                    else:
                        derrotas += 1

                datos_tabla.append({
                    "Equipo": equipo,
                    "PJ": numero_partido,
                    "PG": victorias,
                    "PE": empates,
                    "PP": derrotas,
                    "GF": goles_favor,
                    "GC": goles_contra,
                    "DG": goles_favor - goles_contra,
                    "Pts": puntos
                })

            tabla = pd.DataFrame(datos_tabla)

            indices_partidos = set()

            for equipo in equipos:

                partidos_equipo = partidos_por_equipo[equipo]

                primeros_partidos = partidos_equipo.iloc[:numero_partido]

                indices_partidos.update(
                    primeros_partidos.index
                )

            partidos_considerados = df_temporada[
                df_temporada.index.isin(indices_partidos)
            ].copy()


            tabla = jornadas.ordenar_clasificacion(
                tabla,
                partidos_considerados
            )

            for _, fila in tabla.iterrows():

                evolucion_progresiva.append({
                    "Temporada": nombre_temporada,
                    "Partidos disputados": numero_partido,
                    "Posición": fila["Pos"],
                    "Equipo": fila["Equipo"],
                    "Puntos": fila["Pts"],
                    "Goles a favor": fila["GF"],
                    "Goles en contra": fila["GC"],
                    "Diferencia de goles": fila["DG"]
                })

    tabla_evolucion = pd.DataFrame(evolucion_progresiva)

    tabla_evolucion = tabla_evolucion.sort_values(
        by=[
            "Temporada",
            "Partidos disputados",
            "Posición"
        ]
    ).reset_index(drop=True)


    tabla_cambios = calcular_cambios_entre_etapas(
        tabla_evolucion
    )

    tabla_inicio_mitad_final = calcular_inicio_mitad_final(
        tabla_evolucion
    )


    tabla_resumen = calcular_resumen_por_temporada(
        tabla_evolucion,
        tabla_cambios,
        tabla_inicio_mitad_final
    )

    carpeta_resultados = (
        Path(__file__).resolve().parents[1]
        / "doc"
        / "resultados"
    )
    if not carpeta_resultados.parent.exists():
        carpeta_resultados = (
            Path(__file__).resolve().parent / "resultados"
        )

    carpeta_resultados.mkdir(
        parents=True,
        exist_ok=True
    )

    ruta_resultado = (
        carpeta_resultados
        / "6 - Evolucion de la clasificacion durante una temporada.xlsx"
    )

    with pd.ExcelWriter(
        ruta_resultado,
        engine="openpyxl"
    ) as escritor:

        tabla_evolucion.to_excel(
            escritor,
            sheet_name="Evolución progresiva",
            index=False
        )

        tabla_cambios.to_excel(
            escritor,
            sheet_name="Cambios entre etapas",
            index=False
        )

        tabla_inicio_mitad_final.to_excel(
            escritor,
            sheet_name="Inicio mitad final",
            index=False
        )

        tabla_resumen.to_excel(
            escritor,
            sheet_name="Resumen temporadas",
            index=False
        )

    return (
        tabla_evolucion,
        tabla_cambios,
        tabla_inicio_mitad_final,
        tabla_resumen
    )



print("\n")
print(
    "ANÁLISIS 6 - EVOLUCION DE LA CLASIFICACION POR ETAPAS"
)
(
    tabla_evolucion,
    tabla_cambios,
    tabla_inicio_mitad_final,
    tabla_resumen
) = analizar_evolucion_clasificacion()

print("LISTO!")