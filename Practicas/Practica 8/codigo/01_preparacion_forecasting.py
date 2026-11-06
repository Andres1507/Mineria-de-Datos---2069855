
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


# CONFIGURACION

RUTA_BASE = Path(__file__).resolve().parents[2]

RUTA_DATASET = (
    RUTA_BASE
    / "Dataset"
    / "Dataset Limpio"
    / "dataset_limpio_definitivo.xlsx"
)

RUTA_JORNADAS = (
    RUTA_BASE
    / "Practica 2"
    / "codigo"
    / "jornadas.py"
)

RUTA_SALIDA = (
    RUTA_BASE
    / "Practica 8"
    / "doc"
    / "resultados"
)

CORTES = [5, 10, 15, 19, 25, 30, 35]

PARTIDOS_TEMPORADA = 380
PARTIDOS_EQUIPO = 38


# CARGAR LOGICA DE JORNADAS

def cargar_jornadas():

    if not RUTA_JORNADAS.exists():
        raise FileNotFoundError(
            f"No se encontro jornadas.py: {RUTA_JORNADAS}"
        )

    spec = importlib.util.spec_from_file_location(
        "jornadas",
        RUTA_JORNADAS
    )

    jornadas = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(jornadas)

    return jornadas


# CARGAR Y VALIDAR DATASET

def cargar_datos():

    if not RUTA_DATASET.exists():
        raise FileNotFoundError(
            f"No se encontro el dataset: {RUTA_DATASET}"
        )

    df = pd.read_excel(RUTA_DATASET)

    columnas = [
        "Date", "Time", "HomeTeam", "AwayTeam",
        "FTHG", "FTAG",
        "HS", "AS", "HST", "AST",
        "HC", "AC", "HF", "AF",
        "HY", "AY", "HR", "AR"
    ]

    faltantes = [
        columna for columna in columnas
        if columna not in df.columns
    ]

    if faltantes:
        raise ValueError(
            f"Faltan columnas requeridas: {faltantes}"
        )

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce"
    )

    if df[columnas].isnull().any().any():
        raise ValueError(
            "Existen valores faltantes en las columnas requeridas."
        )

    columnas_numericas = columnas[4:]

    for columna in columnas_numericas:
        df[columna] = pd.to_numeric(
            df[columna],
            errors="raise"
        )

    # IDENTIFICAR TEMPORADAS

    df["AnioInicio"] = (
        df["Date"].dt.year
        - (df["Date"].dt.month < 8).astype(int)
    )

    df["Temporada"] = (
        df["AnioInicio"].astype(str)
        + "-"
        + (df["AnioInicio"] + 1).astype(str).str[-2:]
    )

    return df


# CALCULAR METRICAS PROGRESIVAS DE UN EQUIPO

def construir_progresion(df_temporada, equipo):

    partidos_local = df_temporada[
        df_temporada["HomeTeam"] == equipo
    ]

    partidos_visitante = df_temporada[
        df_temporada["AwayTeam"] == equipo
    ]

    partidos = pd.concat(
        [partidos_local, partidos_visitante]
    ).sort_values(
        ["Date", "Time"],
        kind="mergesort"
    ).copy()

    if len(partidos) != PARTIDOS_EQUIPO:
        raise ValueError(
            f"{equipo}: se encontraron {len(partidos)} partidos."
        )

    es_local = partidos["HomeTeam"].eq(equipo).to_numpy()

    gf = np.where(
        es_local,
        partidos["FTHG"],
        partidos["FTAG"]
    )

    gc = np.where(
        es_local,
        partidos["FTAG"],
        partidos["FTHG"]
    )

    puntos = np.where(
        gf > gc, 3,
        np.where(gf == gc, 1, 0)
    )

    datos = pd.DataFrame({
        "GFPartido": gf,
        "GCPartido": gc,
        "PtsPartido": puntos,
        "PGPartido": (gf > gc).astype(int),
        "PEPartido": (gf == gc).astype(int),
        "PPPartido": (gf < gc).astype(int),

        "TirosPartido": np.where(
            es_local, partidos["HS"], partidos["AS"]
        ),
        "TirosApuertaPartido": np.where(
            es_local, partidos["HST"], partidos["AST"]
        ),
        "CornersPartido": np.where(
            es_local, partidos["HC"], partidos["AC"]
        ),
        "FaltasPartido": np.where(
            es_local, partidos["HF"], partidos["AF"]
        ),
        "AmarillasPartido": np.where(
            es_local, partidos["HY"], partidos["AY"]
        ),
        "RojasPartido": np.where(
            es_local, partidos["HR"], partidos["AR"]
        ),

        "PJLocalPartido": es_local.astype(int),
        "PJVisitantePartido": (~es_local).astype(int),

        "PtsLocalPartido": np.where(es_local, puntos, 0),
        "PtsVisitantePartido": np.where(~es_local, puntos, 0),

        "GFLocalPartido": np.where(es_local, gf, 0),
        "GFVisitantePartido": np.where(~es_local, gf, 0),

        "GCLocalPartido": np.where(es_local, gc, 0),
        "GCVisitantePartido": np.where(~es_local, gc, 0)
    })

    # ACUMULADOS

    columnas_acumuladas = [
        "GF", "GC", "Pts", "PG", "PE", "PP",
        "Tiros", "TirosApuerta", "Corners",
        "Faltas", "Amarillas", "Rojas",
        "PJLocal", "PJVisitante",
        "PtsLocal", "PtsVisitante",
        "GFLocal", "GFVisitante",
        "GCLocal", "GCVisitante"
    ]

    for columna in columnas_acumuladas:

        datos[columna] = datos[
            f"{columna}Partido"
        ].cumsum()

    datos["PJ"] = np.arange(
        1,
        len(datos) + 1
    )

    datos["DG"] = datos["GF"] - datos["GC"]

    # METRICAS POR PARTIDO

    datos["Pts_PJ"] = datos["Pts"] / datos["PJ"]
    datos["GF_PJ"] = datos["GF"] / datos["PJ"]
    datos["GC_PJ"] = datos["GC"] / datos["PJ"]
    datos["DG_PJ"] = datos["DG"] / datos["PJ"]

    datos["Tiros_PJ"] = datos["Tiros"] / datos["PJ"]

    datos["TirosApuerta_PJ"] = (
        datos["TirosApuerta"] / datos["PJ"]
    )

    datos["PrecisionTiro"] = np.where(
        datos["Tiros"] > 0,
        datos["TirosApuerta"] / datos["Tiros"] * 100,
        np.nan
    )

    datos["EfectividadTiro"] = np.where(
        datos["TirosApuerta"] > 0,
        datos["GF"] / datos["TirosApuerta"] * 100,
        np.nan
    )

    datos["Corners_PJ"] = datos["Corners"] / datos["PJ"]
    datos["Faltas_PJ"] = datos["Faltas"] / datos["PJ"]
    datos["Amarillas_PJ"] = datos["Amarillas"] / datos["PJ"]
    datos["Rojas_PJ"] = datos["Rojas"] / datos["PJ"]

    # RENDIMIENTO LOCAL Y VISITANTE

    for condicion in ["Local", "Visitante"]:

        datos[f"Pts_PJ_{condicion}"] = np.where(
            datos[f"PJ{condicion}"] > 0,
            datos[f"Pts{condicion}"] / datos[f"PJ{condicion}"],
            np.nan
        )

        datos[f"GF_PJ_{condicion}"] = np.where(
            datos[f"PJ{condicion}"] > 0,
            datos[f"GF{condicion}"] / datos[f"PJ{condicion}"],
            np.nan
        )

        datos[f"GC_PJ_{condicion}"] = np.where(
            datos[f"PJ{condicion}"] > 0,
            datos[f"GC{condicion}"] / datos[f"PJ{condicion}"],
            np.nan
        )

        datos[f"IndiceExito_{condicion}"] = np.where(
            datos[f"PJ{condicion}"] > 0,
            datos[f"Pts{condicion}"]
            / (datos[f"PJ{condicion}"] * 3) * 100,
            np.nan
        )

    # RENDIMIENTO RECIENTE

    datos["Pts_Ultimos5_PJ"] = (
        datos["PtsPartido"]
        .rolling(5, min_periods=1)
        .mean()
    )

    datos["GF_Ultimos5_PJ"] = (
        datos["GFPartido"]
        .rolling(5, min_periods=1)
        .mean()
    )

    datos["GC_Ultimos5_PJ"] = (
        datos["GCPartido"]
        .rolling(5, min_periods=1)
        .mean()
    )

    return datos


# GENERAR REGISTROS DE TODAS LAS TEMPORADAS

def generar_registros(df, jornadas):

    registros = []
    resumen = []

    temporadas = sorted(df["Temporada"].unique())

    if len(temporadas) != 15:
        raise ValueError(
            f"Se esperaban 15 temporadas y se encontraron {len(temporadas)}."
        )

    for temporada in temporadas:

        df_temporada = df[
            df["Temporada"] == temporada
        ].copy()

        equipos = sorted(
            set(df_temporada["HomeTeam"])
            | set(df_temporada["AwayTeam"])
        )

        if (
            len(df_temporada) != PARTIDOS_TEMPORADA
            or len(equipos) != 20
        ):
            raise ValueError(
                f"Temporada {temporada}: "
                f"{len(df_temporada)} partidos y "
                f"{len(equipos)} equipos."
            )

        datos_equipos = {}
        filas_finales = []

        for equipo in equipos:

            progresion = construir_progresion(
                df_temporada,
                equipo
            )

            datos_equipos[equipo] = progresion

            final = progresion.iloc[-1]

            filas_finales.append({
                "Equipo": equipo,
                "PJ": 38,
                "PG": int(final["PG"]),
                "PE": int(final["PE"]),
                "PP": int(final["PP"]),
                "GF": int(final["GF"]),
                "GC": int(final["GC"]),
                "DG": int(final["DG"]),
                "Pts": int(final["Pts"])
            })

        # CLASIFICACION FINAL CON DESEMPATES DE P2

        tabla_final = pd.DataFrame(filas_finales)

        tabla_final = jornadas.ordenar_clasificacion(
            tabla_final,
            df_temporada
        )

        posiciones = (
            tabla_final
            .set_index("Equipo")["Pos"]
            .to_dict()
        )

        # EXTRAER LOS CORTES DE CADA EQUIPO

        for equipo in equipos:

            progresion = datos_equipos[equipo]
            final = progresion.iloc[-1]

            for corte in CORTES:

                fila = progresion.iloc[corte - 1]

                registro = {
                    "Temporada": temporada,
                    "Equipo": equipo,
                    "PartidosDisputados": corte,

                    "Pts": int(fila["Pts"]),
                    "PG": int(fila["PG"]),
                    "PE": int(fila["PE"]),
                    "PP": int(fila["PP"]),
                    "GF": int(fila["GF"]),
                    "GC": int(fila["GC"]),
                    "DG": int(fila["DG"]),

                    "Pts_PJ": fila["Pts_PJ"],
                    "GF_PJ": fila["GF_PJ"],
                    "GC_PJ": fila["GC_PJ"],
                    "DG_PJ": fila["DG_PJ"],

                    "Tiros_PJ": fila["Tiros_PJ"],
                    "TirosApuerta_PJ": fila["TirosApuerta_PJ"],
                    "PrecisionTiro": fila["PrecisionTiro"],
                    "EfectividadTiro": fila["EfectividadTiro"],

                    "Corners_PJ": fila["Corners_PJ"],
                    "Faltas_PJ": fila["Faltas_PJ"],
                    "Amarillas_PJ": fila["Amarillas_PJ"],
                    "Rojas_PJ": fila["Rojas_PJ"],

                    "Pts_PJ_Local": fila["Pts_PJ_Local"],
                    "Pts_PJ_Visitante": fila["Pts_PJ_Visitante"],
                    "GF_PJ_Local": fila["GF_PJ_Local"],
                    "GF_PJ_Visitante": fila["GF_PJ_Visitante"],
                    "GC_PJ_Local": fila["GC_PJ_Local"],
                    "GC_PJ_Visitante": fila["GC_PJ_Visitante"],
                    "IndiceExito_Local": fila["IndiceExito_Local"],
                    "IndiceExito_Visitante": fila["IndiceExito_Visitante"],

                    "Pts_Ultimos5_PJ": fila["Pts_Ultimos5_PJ"],
                    "GF_Ultimos5_PJ": fila["GF_Ultimos5_PJ"],
                    "GC_Ultimos5_PJ": fila["GC_Ultimos5_PJ"],

                    # VARIABLES OBJETIVO
                    "PuntosFinales": int(final["Pts"]),
                    "PosicionFinal": posiciones[equipo]
                }

                registros.append(registro)

        resumen.append({
            "Temporada": temporada,
            "Partidos": len(df_temporada),
            "Equipos": len(equipos),
            "RegistrosGenerados": len(equipos) * len(CORTES)
        })

        print(
            f"Temporada {temporada}: "
            f"{len(equipos)} equipos procesados."
        )

    return pd.DataFrame(registros), pd.DataFrame(resumen)


# VALIDAR Y EXPORTAR RESULTADOS

def exportar_resultados(datos, resumen):

    RUTA_SALIDA.mkdir(
        parents=True,
        exist_ok=True
    )

    ruta_excel = (
        RUTA_SALIDA
        / "01 - Datos para Forecasting.xlsx"
    )

    with pd.ExcelWriter(
        ruta_excel,
        engine="openpyxl"
    ) as writer:

        datos.to_excel(
            writer,
            sheet_name="Datos progresivos",
            index=False
        )

        resumen.to_excel(
            writer,
            sheet_name="Resumen temporadas",
            index=False
        )

    print(
        f"\nArchivo generado: {ruta_excel}"
    )


# PROCESO PRINCIPAL

def main():

    print("\nPREPARACION DE DATOS PARA FORECASTING")
    print("-" * 50)

    df = cargar_datos()
    jornadas = cargar_jornadas()

    print(f"Partidos cargados: {len(df)}")
    print(f"Temporadas detectadas: {df['Temporada'].nunique()}")

    datos, resumen = generar_registros(
        df,
        jornadas
    )

    # VALIDACIONES FINALES

    registros_esperados = (
        15 * 20 * len(CORTES)
    )

    if len(datos) != registros_esperados:
        raise ValueError(
            f"Se esperaban {registros_esperados} registros "
            f"y se generaron {len(datos)}."
        )

    if datos.duplicated(
        ["Temporada", "Equipo", "PartidosDisputados"]
    ).any():
        raise ValueError(
            "Se encontraron registros duplicados."
        )

    if datos.isnull().any().any():
        print(
            "\nADVERTENCIA: existen valores nulos en algunas métricas."
        )
        print(
            datos.isnull().sum()[
                datos.isnull().sum() > 0
            ]
        )

    exportar_resultados(
        datos,
        resumen
    )

    print("\nPROCESO COMPLETADO")
    print("-" * 50)
    print(f"Temporadas: {datos['Temporada'].nunique()}")
    print(f"Equipos-temporada: {datos.groupby(['Temporada', 'Equipo']).ngroups}")
    print(f"Cortes evaluados: {len(CORTES)}")
    print(f"Registros generados: {len(datos)}")


if __name__ == "__main__":
    main()
