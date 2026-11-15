
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error

# CONFIGURACION
BASE_DIR = Path(__file__).resolve().parents[1]

RUTA_PREDICCIONES = BASE_DIR / "doc" / "resultados" / "02 - Resultados Forecasting.xlsx"
RUTA_DATOS = BASE_DIR / "doc" / "resultados" / "01 - Datos para Forecasting.xlsx"
RUTA_SALIDA = BASE_DIR / "doc" / "resultados" / "03 - Evaluacion Clasificacion.xlsx"

ZONAS = ["1-5", "6-10", "11-15", "16-20"]
CLAVES = ["Temporada", "Equipo", "PartidosDisputados"]


# CARGA DE DATOS
def cargar_datos():
    predicciones = pd.read_excel(
        RUTA_PREDICCIONES,
        sheet_name="Predicciones"
    )

    datos = pd.read_excel(
        RUTA_DATOS,
        sheet_name="Datos progresivos"
    )

    columnas = CLAVES + ["Pts", "DG", "GF", "PosicionFinal"]
    datos = datos[columnas]

    df = predicciones.merge(
        datos,
        on=CLAVES,
        how="left",
        validate="many_to_one"
    )

    if df[["PosicionFinal", "Pts", "DG", "GF"]].isnull().any().any():
        raise ValueError("Existen registros sin informacion para evaluar.")

    return df


# CLASIFICACION POR ZONAS
def obtener_zona(posicion):
    if posicion <= 5:
        return "1-5"
    elif posicion <= 10:
        return "6-10"
    elif posicion <= 15:
        return "11-15"
    return "16-20"


# POSICIONES ESTIMADAS
def calcular_posiciones(df):
    resultados = []

    grupos = df.groupby(
        ["Temporada", "PartidosDisputados", "Modelo"]
    )

    for _, grupo in grupos:
        grupo = grupo.sort_values(
            ["PuntosPredichos", "Pts", "DG", "GF"],
            ascending=False,
            kind="mergesort"
        ).copy()

        grupo["PosicionPredicha"] = range(1, len(grupo) + 1)

        grupo["ZonaReal"] = grupo["PosicionFinal"].apply(obtener_zona)
        grupo["ZonaPredicha"] = grupo["PosicionPredicha"].apply(obtener_zona)

        resultados.append(grupo)

    return pd.concat(resultados, ignore_index=True)


# METRICAS GENERALES
def calcular_metricas_generales(df):
    resultados = []

    for (corte, modelo), grupo in df.groupby(
        ["PartidosDisputados", "Modelo"]
    ):
        reales = grupo["PosicionFinal"]
        estimadas = grupo["PosicionPredicha"]

        resultados.append({
            "PartidosDisputados": corte,
            "Modelo": modelo,
            "MAE_Posicion": mean_absolute_error(reales, estimadas),
            "RMSE_Posicion": np.sqrt(
                mean_squared_error(reales, estimadas)
            ),
            "Exactitud_Posicion": (
                reales == estimadas
            ).mean() * 100,
            "Exactitud_Zona": (
                grupo["ZonaReal"] == grupo["ZonaPredicha"]
            ).mean() * 100,
            "Equipos": len(grupo)
        })

    return pd.DataFrame(resultados)


# METRICAS POR ZONA REAL
def calcular_metricas_zona(df):
    resultados = []

    for (corte, modelo, zona), grupo in df.groupby(
        ["PartidosDisputados", "Modelo", "ZonaReal"]
    ):
        resultados.append({
            "PartidosDisputados": corte,
            "Modelo": modelo,
            "ZonaReal": zona,
            "MAE_Posicion": mean_absolute_error(
                grupo["PosicionFinal"],
                grupo["PosicionPredicha"]
            ),
            "Exactitud_Zona": (
                grupo["ZonaReal"] == grupo["ZonaPredicha"]
            ).mean() * 100,
            "Equipos": len(grupo)
        })

    return pd.DataFrame(resultados)


# MATRICES DE CONFUSION
def calcular_matrices(df):
    resultados = []

    for (corte, modelo), grupo in df.groupby(
        ["PartidosDisputados", "Modelo"]
    ):
        matriz = pd.crosstab(
            grupo["ZonaReal"],
            grupo["ZonaPredicha"]
        ).reindex(
            index=ZONAS,
            columns=ZONAS,
            fill_value=0
        )

        matriz = matriz.reset_index()
        matriz.insert(0, "Modelo", modelo)
        matriz.insert(0, "PartidosDisputados", corte)

        resultados.append(matriz)

    return pd.concat(resultados, ignore_index=True)


# EXPORTACION
def exportar_resultados(
    predicciones,
    metricas,
    metricas_zona,
    matrices
):
    with pd.ExcelWriter(RUTA_SALIDA, engine="openpyxl") as writer:
        predicciones.to_excel(
            writer,
            sheet_name="Posiciones estimadas",
            index=False
        )

        metricas.to_excel(
            writer,
            sheet_name="Metricas generales",
            index=False
        )

        metricas_zona.to_excel(
            writer,
            sheet_name="Metricas por zona",
            index=False
        )

        matrices.to_excel(
            writer,
            sheet_name="Matrices confusion",
            index=False
        )


# PROGRAMA PRINCIPAL
def main():
    print("EVALUACION DE LA CLASIFICACION")
    print("-" * 40)

    df = cargar_datos()
    print(f"Predicciones cargadas: {len(df)}")

    predicciones = calcular_posiciones(df)

    metricas = calcular_metricas_generales(predicciones)
    metricas_zona = calcular_metricas_zona(predicciones)
    matrices = calcular_matrices(predicciones)

    exportar_resultados(
        predicciones,
        metricas,
        metricas_zona,
        matrices
    )

    print("\nMETRICAS GENERALES")
    print(
        metricas.sort_values(
            ["PartidosDisputados", "MAE_Posicion"]
        ).to_string(index=False)
    )

    print(f"\nPredicciones evaluadas: {len(predicciones)}")
    print(f"Modelos: {predicciones['Modelo'].nunique()}")
    print(f"Cortes: {predicciones['PartidosDisputados'].nunique()}")

    print(f"\nArchivo generado: {RUTA_SALIDA}")
    print("PROCESO COMPLETADO")


if __name__ == "__main__":
    main()
