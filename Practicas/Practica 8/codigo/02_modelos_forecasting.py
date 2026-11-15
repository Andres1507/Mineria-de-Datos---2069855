
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error

# CONFIGURACION
BASE_DIR = Path(__file__).resolve().parents[1]
RUTA_ENTRADA = BASE_DIR / "doc" / "resultados" / "01 - Datos para Forecasting.xlsx"
RUTA_SALIDA = BASE_DIR / "doc" / "resultados" / "02 - Resultados Forecasting.xlsx"

CORTES = [5, 10, 15, 19, 25, 30, 35]
MODELOS = ["E0 - Extrapolacion", "E1 - Regresion simple", "E2 - Regresion multiple"]

VARIABLE_OBJETIVO = "PuntosFinales"
VARIABLES_E1 = ["Pts_PJ"]
VARIABLES_E2 = ["Pts_PJ", "GF_PJ", "GC_PJ"]

# CARGA DE DATOS
def cargar_datos():
    if not RUTA_ENTRADA.exists():
        raise FileNotFoundError(f"No se encontro el archivo: {RUTA_ENTRADA}")

    df = pd.read_excel(RUTA_ENTRADA, sheet_name="Datos progresivos")

    columnas = [
        "Temporada", "Equipo", "PartidosDisputados",
        "Pts_PJ", "GF_PJ", "GC_PJ", VARIABLE_OBJETIVO
    ]

    faltantes = [col for col in columnas if col not in df.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas necesarias: {faltantes}")

    if df[columnas].isnull().any().any():
        raise ValueError("Existen valores faltantes en las columnas utilizadas.")

    return df


# GENERACION DE PREDICCIONES
def generar_predicciones(df):
    temporadas = sorted(df["Temporada"].unique())
    resultados = []

    # VALIDACION CRONOLOGICA
    for i in range(5, len(temporadas)):
        temporada_test = temporadas[i]
        temporadas_train = temporadas[:i]

        for corte in CORTES:
            entrenamiento = df[
                (df["Temporada"].isin(temporadas_train)) &
                (df["PartidosDisputados"] == corte)
            ]

            prueba = df[
                (df["Temporada"] == temporada_test) &
                (df["PartidosDisputados"] == corte)
            ].copy()

            if entrenamiento.empty or prueba.empty:
                continue

            # E0: EXTRAPOLACION DIRECTA
            prueba["E0 - Extrapolacion"] = prueba["Pts_PJ"] * 38

            # E1: REGRESION LINEAL SIMPLE
            modelo_e1 = LinearRegression()
            modelo_e1.fit(
                entrenamiento[VARIABLES_E1],
                entrenamiento[VARIABLE_OBJETIVO]
            )
            prueba["E1 - Regresion simple"] = modelo_e1.predict(
                prueba[VARIABLES_E1]
            )

            # E2: REGRESION LINEAL MULTIPLE
            modelo_e2 = LinearRegression()
            modelo_e2.fit(
                entrenamiento[VARIABLES_E2],
                entrenamiento[VARIABLE_OBJETIVO]
            )
            prueba["E2 - Regresion multiple"] = modelo_e2.predict(
                prueba[VARIABLES_E2]
            )

            # GUARDAR RESULTADOS
            for _, fila in prueba.iterrows():
                for modelo in MODELOS:
                    prediccion = fila[modelo]
                    real = fila[VARIABLE_OBJETIVO]

                    resultados.append({
                        "Temporada": temporada_test,
                        "Equipo": fila["Equipo"],
                        "PartidosDisputados": corte,
                        "Modelo": modelo,
                        "PuntosReales": real,
                        "PuntosPredichos": prediccion,
                        "Error": prediccion - real,
                        "ErrorAbsoluto": abs(prediccion - real),
                        "TemporadasEntrenamiento": 0 if modelo == MODELOS[0] else len(temporadas_train)
                    })

    return pd.DataFrame(resultados)


# EVALUACION DE MODELOS
def calcular_metricas(predicciones):
    metricas = []

    # METRICAS GENERALES POR CORTE
    for (corte, modelo), grupo in predicciones.groupby(
        ["PartidosDisputados", "Modelo"]
    ):
        reales = grupo["PuntosReales"]
        estimados = grupo["PuntosPredichos"]

        metricas.append({
            "PartidosDisputados": corte,
            "Modelo": modelo,
            "MAE": mean_absolute_error(reales, estimados),
            "RMSE": np.sqrt(mean_squared_error(reales, estimados)),
            "ErrorPromedio": (estimados - reales).mean(),
            "Registros": len(grupo)
        })

    metricas_corte = pd.DataFrame(metricas)

    # METRICAS POR TEMPORADA
    metricas_temporada = []

    for (temporada, corte, modelo), grupo in predicciones.groupby(
        ["Temporada", "PartidosDisputados", "Modelo"]
    ):
        reales = grupo["PuntosReales"]
        estimados = grupo["PuntosPredichos"]

        metricas_temporada.append({
            "Temporada": temporada,
            "PartidosDisputados": corte,
            "Modelo": modelo,
            "MAE": mean_absolute_error(reales, estimados),
            "RMSE": np.sqrt(mean_squared_error(reales, estimados)),
            "ErrorPromedio": (estimados - reales).mean(),
            "Registros": len(grupo)
        })

    metricas_temporada = pd.DataFrame(metricas_temporada)

    return metricas_corte, metricas_temporada


# EXPORTACION
def exportar_resultados(predicciones, metricas_corte, metricas_temporada):
    with pd.ExcelWriter(RUTA_SALIDA, engine="openpyxl") as writer:
        predicciones.to_excel(
            writer, sheet_name="Predicciones", index=False
        )
        metricas_corte.to_excel(
            writer, sheet_name="Metricas por corte", index=False
        )
        metricas_temporada.to_excel(
            writer, sheet_name="Metricas por temporada", index=False
        )


# PROGRAMA PRINCIPAL
def main():
    print("MODELOS DE FORECASTING")
    print("-" * 40)

    df = cargar_datos()
    print(f"Registros cargados: {len(df)}")

    predicciones = generar_predicciones(df)

    if predicciones.empty:
        raise ValueError("No se generaron predicciones.")

    metricas_corte, metricas_temporada = calcular_metricas(predicciones)

    exportar_resultados(
        predicciones,
        metricas_corte,
        metricas_temporada
    )

    print("\nRESULTADOS")
    print(f"Predicciones generadas: {len(predicciones)}")
    print(f"Temporadas evaluadas: {predicciones['Temporada'].nunique()}")
    print(f"Cortes evaluados: {predicciones['PartidosDisputados'].nunique()}")

    print("\nMETRICAS GENERALES")
    print(
        metricas_corte.sort_values(
            ["PartidosDisputados", "MAE"]
        ).to_string(index=False)
    )

    print(f"\nArchivo generado: {RUTA_SALIDA}")
    print("PROCESO COMPLETADO")


if __name__ == "__main__":
    main()
