import pandas as pd
import numpy as np
from pathlib import Path
from scipy.stats import spearmanr
from sklearn.metrics import mean_absolute_error

# CONFIGURACION
BASE_DIR = Path(__file__).resolve().parents[1]

RUTA_PREDICCIONES = BASE_DIR / "doc" / "resultados" / "02 - Resultados Forecasting.xlsx"
RUTA_CLASIFICACION = BASE_DIR / "doc" / "resultados" / "03 - Evaluacion Clasificacion.xlsx"
RUTA_SALIDA = BASE_DIR / "doc" / "resultados" / "04 - Predictibilidad y Competitividad.xlsx"

CORTES = [5, 10, 15, 19, 25, 30, 35]

# INDICADORES HISTORICOS DE P2
# DESVIACION ESTANDAR Y RANGO DE PUNTOS POR TEMPORADA
DATOS_DISPERSION = [
    ["2011-12", 16.74, 73],
    ["2012-13", 17.75, 66],
    ["2013-14", 18.29, 65],
    ["2014-15", 20.81, 74],
    ["2015-16", 18.10, 59],
    ["2016-17", 20.63, 73],
    ["2017-18", 18.23, 73],
    ["2018-19", 13.91, 55],
    ["2019-20", 16.13, 62],
    ["2020-21", 17.84, 56],
    ["2021-22", 15.24, 55],
    ["2022-23", 15.88, 63],
    ["2023-24", 20.37, 74],
    ["2024-25", 17.90, 72],
    ["2025-26", 16.23, 65]
]

# MOVILIDAD ENTRE ZONAS DE P2
# MISMA ZONA, SUBEN Y BAJAN
DATOS_MOVILIDAD = [
    ["2012-13", 7, 5, 5],
    ["2013-14", 6, 4, 7],
    ["2014-15", 9, 4, 4],
    ["2015-16", 6, 5, 6],
    ["2016-17", 9, 3, 5],
    ["2017-18", 8, 2, 7],
    ["2018-19", 8, 5, 4],
    ["2019-20", 7, 3, 7],
    ["2020-21", 7, 4, 6],
    ["2021-22", 8, 4, 5],
    ["2022-23", 8, 4, 5],
    ["2023-24", 8, 3, 6],
    ["2024-25", 7, 5, 5],
    ["2025-26", 9, 5, 3]
]


# CARGA DE INDICADORES
def cargar_competitividad():
    dispersion = pd.DataFrame(
        DATOS_DISPERSION,
        columns=["Temporada", "DesvEstandar", "Rango"]
    )

    movilidad = pd.DataFrame(
        DATOS_MOVILIDAD,
        columns=["Temporada", "MismaZona", "Suben", "Bajan"]
    )

    movilidad["EquiposComparables"] = (
        movilidad[["MismaZona", "Suben", "Bajan"]].sum(axis=1)
    )

    movilidad["MovilidadPct"] = (
        (movilidad["Suben"] + movilidad["Bajan"]) /
        movilidad["EquiposComparables"] * 100
    )

    return dispersion.merge(
        movilidad,
        on="Temporada",
        how="left"
    )


# CALCULO DE ERRORES POR TEMPORADA
def calcular_errores():
    predicciones = pd.read_excel(
        RUTA_PREDICCIONES,
        sheet_name="Predicciones"
    )

    posiciones = pd.read_excel(
        RUTA_CLASIFICACION,
        sheet_name="Posiciones estimadas"
    )

    errores_puntos = predicciones.groupby(
        ["Temporada", "PartidosDisputados", "Modelo"]
    ).agg(
        MAE_Puntos=("ErrorAbsoluto", "mean"),
        RMSE_Puntos=("Error", lambda x: np.sqrt(np.mean(x ** 2))),
        ErrorPromedio=("Error", "mean")
    ).reset_index()

    errores_posicion = posiciones.groupby(
        ["Temporada", "PartidosDisputados", "Modelo"]
    ).agg(
        MAE_Posicion=(
            "PosicionPredicha",
            lambda x: mean_absolute_error(
                posiciones.loc[x.index, "PosicionFinal"], x
            )
        ),
        Exactitud_Posicion=(
            "PosicionPredicha",
            lambda x: (
                x == posiciones.loc[x.index, "PosicionFinal"]
            ).mean() * 100
        ),
        Exactitud_Zona=(
            "ZonaPredicha",
            lambda x: (
                x == posiciones.loc[x.index, "ZonaReal"]
            ).mean() * 100
        )
    ).reset_index()

    return errores_puntos.merge(
        errores_posicion,
        on=["Temporada", "PartidosDisputados", "Modelo"],
        validate="one_to_one"
    )


# RELACION ENTRE COMPETITIVIDAD Y ERROR
def calcular_correlaciones(errores):
    indicadores = cargar_competitividad()

    datos = errores.merge(
        indicadores,
        on="Temporada",
        how="left",
        validate="many_to_one"
    )

    variables_competitividad = [
        "DesvEstandar",
        "Rango",
        "MovilidadPct"
    ]

    variables_predictibilidad = [
        "MAE_Puntos",
        "MAE_Posicion",
        "Exactitud_Zona"
    ]

    resultados = []

    for (corte, modelo), grupo in datos.groupby(
        ["PartidosDisputados", "Modelo"]
    ):
        for indicador in variables_competitividad:
            for metrica in variables_predictibilidad:
                muestra = grupo[[indicador, metrica]].dropna()

                if len(muestra) < 3:
                    continue

                rho, pvalor = spearmanr(
                    muestra[indicador],
                    muestra[metrica]
                )

                resultados.append({
                    "PartidosDisputados": corte,
                    "Modelo": modelo,
                    "IndicadorCompetitividad": indicador,
                    "MetricaPredictibilidad": metrica,
                    "Spearman": rho,
                    "ValorP": pvalor,
                    "Temporadas": len(muestra)
                })

    return datos, pd.DataFrame(resultados)


# RESUMEN GENERAL POR MODELO
def calcular_resumen(datos):
    return datos.groupby(
        ["PartidosDisputados", "Modelo"]
    ).agg(
        MAE_Puntos_Promedio=("MAE_Puntos", "mean"),
        MAE_Posicion_Promedio=("MAE_Posicion", "mean"),
        Exactitud_Zona_Promedio=("Exactitud_Zona", "mean"),
        DesvEstandar_Promedio=("DesvEstandar", "mean"),
        Rango_Promedio=("Rango", "mean"),
        Movilidad_Promedio=("MovilidadPct", "mean"),
        Temporadas=("Temporada", "nunique")
    ).reset_index()


# EXPORTACION
def exportar_resultados(
    datos,
    indicadores,
    correlaciones,
    resumen
):
    with pd.ExcelWriter(RUTA_SALIDA, engine="openpyxl") as writer:
        datos.to_excel(
            writer,
            sheet_name="Errores por temporada",
            index=False
        )

        indicadores.to_excel(
            writer,
            sheet_name="Indicadores competitivos",
            index=False
        )

        correlaciones.to_excel(
            writer,
            sheet_name="Correlaciones",
            index=False
        )

        resumen.to_excel(
            writer,
            sheet_name="Resumen general",
            index=False
        )


# PROGRAMA PRINCIPAL
def main():
    print("RELACION ENTRE PREDICTIBILIDAD Y COMPETITIVIDAD")
    print("-" * 55)

    errores = calcular_errores()
    indicadores = cargar_competitividad()

    datos, correlaciones = calcular_correlaciones(errores)
    resumen = calcular_resumen(datos)

    exportar_resultados(
        datos,
        indicadores,
        correlaciones,
        resumen
    )

    print(f"Registros evaluados: {len(datos)}")
    print(f"Temporadas evaluadas: {datos['Temporada'].nunique()}")
    print(f"Correlaciones calculadas: {len(correlaciones)}")

    print("\nRESUMEN DE PREDICTIBILIDAD")
    print(resumen.to_string(index=False))

    print("\nCORRELACIONES CON MAE DE PUNTOS")
    print(
        correlaciones[
            correlaciones["MetricaPredictibilidad"] == "MAE_Puntos"
        ].sort_values(
            ["PartidosDisputados", "Spearman"]
        ).to_string(index=False)
    )

    print(f"\nArchivo generado: {RUTA_SALIDA}")
    print("PROCESO COMPLETADO")


if __name__ == "__main__":
    main()
