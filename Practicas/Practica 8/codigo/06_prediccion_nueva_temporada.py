
import pandas as pd
from pathlib import Path
from sklearn.linear_model import LinearRegression

# CONFIGURACION
TEMPORADA = "2026-27"
CORTE = 10
PARTIDOS_TEMPORADA = 38

# RUTAS
BASE_DIR = Path(__file__).resolve().parents[1]
RUTA_HISTORICO = BASE_DIR / "doc" / "resultados" / "01 - Datos para Forecasting.xlsx"
RUTA_NUEVA = BASE_DIR / "doc" / "resultados" / f"Resultados {TEMPORADA}.xlsx"
RUTA_SALIDA = BASE_DIR / "doc" / "resultados" / f"06 - Prediccion {TEMPORADA}.xlsx"

# CARGAR HISTORICO
historico = pd.read_excel(
    RUTA_HISTORICO,
    sheet_name="Datos progresivos"
)

entrenamiento = historico[
    historico["PartidosDisputados"] == CORTE
].copy()

entrenamiento = entrenamiento.dropna(
    subset=["Pts_PJ", "GF_PJ", "GC_PJ", "PuntosFinales"]
)

# ENTRENAR MODELOS
X1 = entrenamiento[["Pts_PJ"]]
X2 = entrenamiento[["Pts_PJ", "GF_PJ", "GC_PJ"]]
y = entrenamiento["PuntosFinales"]

modelo_e1 = LinearRegression().fit(X1, y)
modelo_e2 = LinearRegression().fit(X2, y)

# CARGAR RESULTADOS NUEVOS
partidos = pd.read_excel(RUTA_NUEVA)

columnas = ["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG"]

if not set(columnas).issubset(partidos.columns):
    raise ValueError("El archivo nuevo no contiene todas las columnas necesarias.")

partidos["Date"] = pd.to_datetime(partidos["Date"])
partidos["FTHG"] = pd.to_numeric(partidos["FTHG"], errors="coerce")
partidos["FTAG"] = pd.to_numeric(partidos["FTAG"], errors="coerce")

partidos = partidos.dropna(subset=columnas).copy()

if "Time" in partidos.columns:
    partidos = partidos.sort_values(["Date", "Time"])
else:
    partidos = partidos.sort_values("Date")

# CONSTRUIR RENDIMIENTO POR EQUIPO
rendimiento = {}

for _, partido in partidos.iterrows():
    local = partido["HomeTeam"]
    visitante = partido["AwayTeam"]
    gf_local = int(partido["FTHG"])
    gf_visitante = int(partido["FTAG"])

    if local not in rendimiento:
        rendimiento[local] = []

    if visitante not in rendimiento:
        rendimiento[visitante] = []

    if gf_local > gf_visitante:
        puntos_local, puntos_visitante = 3, 0
    elif gf_local < gf_visitante:
        puntos_local, puntos_visitante = 0, 3
    else:
        puntos_local, puntos_visitante = 1, 1

    rendimiento[local].append(
        (puntos_local, gf_local, gf_visitante)
    )

    rendimiento[visitante].append(
        (puntos_visitante, gf_visitante, gf_local)
    )

# CALCULAR METRICAS DEL CORTE
registros = []

for equipo, resultados in rendimiento.items():
    if len(resultados) < CORTE:
        continue

    resultados = resultados[:CORTE]

    puntos = sum(r[0] for r in resultados)
    gf = sum(r[1] for r in resultados)
    gc = sum(r[2] for r in resultados)

    registros.append({
        "Temporada": TEMPORADA,
        "Equipo": equipo,
        "PartidosDisputados": CORTE,
        "Pts": puntos,
        "GF": gf,
        "GC": gc,
        "Pts_PJ": puntos / CORTE,
        "GF_PJ": gf / CORTE,
        "GC_PJ": gc / CORTE
    })

datos = pd.DataFrame(registros)

if datos.empty:
    raise ValueError(
        f"No hay equipos con al menos {CORTE} partidos disputados."
    )

# GENERAR PREDICCIONES
datos["E0 - Extrapolacion"] = (
    datos["Pts_PJ"] * PARTIDOS_TEMPORADA
)

datos["E1 - Regresion simple"] = modelo_e1.predict(
    datos[["Pts_PJ"]]
)

datos["E2 - Regresion multiple"] = modelo_e2.predict(
    datos[["Pts_PJ", "GF_PJ", "GC_PJ"]]
)

# CALCULAR POSICIONES Y ZONAS
predicciones = []

for modelo in [
    "E0 - Extrapolacion",
    "E1 - Regresion simple",
    "E2 - Regresion multiple"
]:
    resultado = datos[
        ["Temporada", "Equipo", "PartidosDisputados", modelo]
    ].copy()

    resultado = resultado.rename(
        columns={modelo: "PuntosEstimados"}
    )

    resultado = resultado.sort_values(
        "PuntosEstimados",
        ascending=False
    ).reset_index(drop=True)

    resultado["PosicionPredicha"] = resultado.index + 1
    resultado["Modelo"] = modelo

    resultado["ZonaPredicha"] = pd.cut(
        resultado["PosicionPredicha"],
        bins=[0, 5, 10, 15, 20],
        labels=["1-5", "6-10", "11-15", "16-20"]
    )

    predicciones.append(resultado)

predicciones = pd.concat(predicciones, ignore_index=True)

# EXPORTAR RESULTADOS
with pd.ExcelWriter(RUTA_SALIDA, engine="openpyxl") as writer:
    datos.to_excel(
        writer,
        sheet_name="Datos del corte",
        index=False
    )

    predicciones.to_excel(
        writer,
        sheet_name="Predicciones",
        index=False
    )

print("PREDICCION GENERADA CORRECTAMENTE")
print(f"Temporada: {TEMPORADA}")
print(f"Partidos por equipo: {CORTE}")
print(f"Equipos evaluados: {len(datos)}")
print(f"Modelos utilizados: 3")
print(f"Archivo generado: {RUTA_SALIDA}")
