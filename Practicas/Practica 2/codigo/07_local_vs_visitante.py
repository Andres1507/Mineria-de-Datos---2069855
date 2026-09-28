from pathlib import Path
import pandas as pd


def analizar_local_vs_visitante():

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
        / "7 - Rendimiento Local y Visitante.xlsx"
    )

    df = pd.read_excel(ruta_dataset)

    if len(df) != 5700:
        raise ValueError(
            f"Se esperaban 5700 partidos, pero se encontraron {len(df)}."
        )



    #Cada partido genera un registro para local y otro para visitante y conserva las demas estadisticas

    registros = []

    for _, partido in df.iterrows():

        # EQUIPO LOCAL
        if partido["FTR"] == "H":
            victorias = 1
            empates = 0
            derrotas = 0
            puntos = 3

        elif partido["FTR"] == "D":
            victorias = 0
            empates = 1
            derrotas = 0
            puntos = 1

        else:
            victorias = 0
            empates = 0
            derrotas = 1
            puntos = 0

        registros.append({
            "Equipo": partido["HomeTeam"],
            "Condición": "Local",
            "PJ": 1,
            "PG": victorias,
            "PE": empates,
            "PP": derrotas,
            "GF": partido["FTHG"],
            "GC": partido["FTAG"],
            "Tiros": partido["HS"],
            "Tiros a puerta": partido["HST"],
            "Córners": partido["HC"],
            "Faltas": partido["HF"],
            "Amarillas": partido["HY"],
            "Rojas": partido["HR"],
            "Puntos": puntos
        })

        # EQUIPO VISITANTE
        if partido["FTR"] == "A":
            victorias = 1
            empates = 0
            derrotas = 0
            puntos = 3

        elif partido["FTR"] == "D":
            victorias = 0
            empates = 1
            derrotas = 0
            puntos = 1

        else:
            victorias = 0
            empates = 0
            derrotas = 1
            puntos = 0

        registros.append({
            "Equipo": partido["AwayTeam"],
            "Condición": "Visitante",
            "PJ": 1,
            "PG": victorias,
            "PE": empates,
            "PP": derrotas,
            "GF": partido["FTAG"],
            "GC": partido["FTHG"],
            "Tiros": partido["AS"],
            "Tiros a puerta": partido["AST"],
            "Córners": partido["AC"],
            "Faltas": partido["AF"],
            "Amarillas": partido["AY"],
            "Rojas": partido["AR"],
            "Puntos": puntos
        })

    registros_df = pd.DataFrame(registros)

    # AGRUPAR POR EQUIPO Y CONDICIÓN
    metricas = [
        "PJ",
        "PG",
        "PE",
        "PP",
        "GF",
        "GC",
        "Tiros",
        "Tiros a puerta",
        "Córners",
        "Faltas",
        "Amarillas",
        "Rojas",
        "Puntos"
    ]

    agrupado = (
        registros_df
        .groupby(["Equipo", "Condición"])[metricas]
        .sum()
        .reset_index()
    )

    # SEPARAR LOCAL Y VISITANTE
    resumen = agrupado.pivot(
        index="Equipo",
        columns="Condición",
        values=metricas
    )

    resumen.columns = [
        f"{metrica} {condicion}"
        for metrica, condicion in resumen.columns
    ]

    resumen = resumen.reset_index()

    # TOTALES DEL EQUIPO
    for metrica in metricas:
        resumen[f"{metrica} Total"] = (
            resumen[f"{metrica} Local"]
            + resumen[f"{metrica} Visitante"]
        )

    # 7. PROMEDIOS POR PARTIDO
    metricas_por_partido = [
        "Puntos",
        "GF",
        "GC",
        "Tiros",
        "Tiros a puerta",
        "Córners",
        "Faltas",
        "Amarillas",
        "Rojas"
    ]

    for metrica in metricas_por_partido:

        resumen[f"{metrica}/PJ Local"] = (
            resumen[f"{metrica} Local"]
            / resumen["PJ Local"]
        ).round(3)

        resumen[f"{metrica}/PJ Visitante"] = (
            resumen[f"{metrica} Visitante"]
            / resumen["PJ Visitante"]
        ).round(3)

        resumen[f"Dif. {metrica}/PJ"] = (
            resumen[f"{metrica}/PJ Local"]
            - resumen[f"{metrica}/PJ Visitante"]
        ).round(3)

    """

    indice de exito: (puntos obtenidos/ptos posibles)* (100)
    """
    
    

    for condicion in ["Local", "Visitante"]:

        resumen[f"% Victorias {condicion}"] = (
            resumen[f"PG {condicion}"]
            / resumen[f"PJ {condicion}"]
            * 100
        ).round(2)

        resumen[f"Índice de éxito {condicion}"] = (
            resumen[f"Puntos {condicion}"]
            / (resumen[f"PJ {condicion}"] * 3)
            * 100
        ).round(2)

    resumen["Dif. índice de éxito"] = (
        resumen["Índice de éxito Local"]
        - resumen["Índice de éxito Visitante"]
    ).round(2)


    resumen["DG/PJ Local"] = (
        resumen["GF/PJ Local"]
        - resumen["GC/PJ Local"]
    ).round(3)

    resumen["DG/PJ Visitante"] = (
        resumen["GF/PJ Visitante"]
        - resumen["GC/PJ Visitante"]
    ).round(3)

    """
        EFECTIVIDAD DE TIRO: ( Goles / tiros a puerta) * 100
    """

    for condicion in ["Local", "Visitante"]:

        resumen[f"Efectividad de tiro {condicion}"] = (
            resumen[f"GF {condicion}"]
            / resumen[f"Tiros a puerta {condicion}"]
            * 100
        ).round(2)

    resumen["Dif. efectividad de tiro"] = (
        resumen["Efectividad de tiro Local"]
        - resumen["Efectividad de tiro Visitante"]
    ).round(2)

    # IDENTIFICAR LA MEJOR CONDICIÓN

    resumen["Mejor condición por éxito"] = resumen.apply(
        lambda fila:
            "Local"
            if fila["Índice de éxito Local"]
            > fila["Índice de éxito Visitante"]
            else (
                "Visitante"
                if fila["Índice de éxito Visitante"]
                > fila["Índice de éxito Local"]
                else "Igual"
            ),
        axis=1
    )

    resumen["Mejor condición por goles"] = resumen.apply(
        lambda fila:
            "Local"
            if fila["GF/PJ Local"]
            > fila["GF/PJ Visitante"]
            else (
                "Visitante"
                if fila["GF/PJ Visitante"]
                > fila["GF/PJ Local"]
                else "Igual"
            ),
        axis=1
    )

    resumen = (
        resumen
        .sort_values("Equipo")
        .reset_index(drop=True)
    )


    tabla_reporte = resumen[
        [
            "Equipo",
            "PJ Total",

            "PG Local",
            "PE Local",
            "PP Local",

            "PG Visitante",
            "PE Visitante",
            "PP Visitante",

            "Índice de éxito Local",
            "Índice de éxito Visitante",
            "Dif. índice de éxito",

            "GF/PJ Local",
            "GF/PJ Visitante",

            "GC/PJ Local",
            "GC/PJ Visitante",

            "Tiros a puerta/PJ Local",
            "Tiros a puerta/PJ Visitante",

            "Efectividad de tiro Local",
            "Efectividad de tiro Visitante",

            "Mejor condición por éxito",
            "Mejor condición por goles"
        ]
    ].copy()

    perfil = resumen[
        [
            "Equipo",

            "PJ Total",
            "PJ Local",
            "PJ Visitante",

            "Puntos Total",
            "Puntos Local",
            "Puntos Visitante",

            "Índice de éxito Local",
            "Índice de éxito Visitante",
            "Dif. índice de éxito",

            "GF Total",
            "GF/PJ Local",
            "GF/PJ Visitante",

            "GC/PJ Local",
            "GC/PJ Visitante",

            "Tiros/PJ Local",
            "Tiros/PJ Visitante",

            "Tiros a puerta/PJ Local",
            "Tiros a puerta/PJ Visitante",

            "Efectividad de tiro Local",
            "Efectividad de tiro Visitante",
            "Dif. efectividad de tiro",

            "Córners/PJ Local",
            "Córners/PJ Visitante",

            "Faltas/PJ Local",
            "Faltas/PJ Visitante",

            "Amarillas/PJ Local",
            "Amarillas/PJ Visitante",

            "Rojas/PJ Local",
            "Rojas/PJ Visitante",

            "Mejor condición por éxito",
            "Mejor condición por goles"
        ]
    ].copy()


    with pd.ExcelWriter(
        ruta_salida,
        engine="openpyxl"
    ) as writer:

        resumen.to_excel(
            writer,
            sheet_name="Análisis completo",
            index=False
        )

        tabla_reporte.to_excel(
            writer,
            sheet_name="Resumen",
            index=False
        )

        perfil.to_excel(
            writer,
            sheet_name="Perfil por equipo",
            index=False
        )


    return resumen, tabla_reporte, perfil


print("\n")
print(
    "ANÁLISIS 7 - RENDIMIENTO DE LOCAL VS VISITANTE"
)

analizar_local_vs_visitante()


print("LISTO!")

