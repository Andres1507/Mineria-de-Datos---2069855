from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

# RUTAS
carpeta_script = Path(__file__).resolve().parent
carpeta_practica = carpeta_script.parent
archivo_excel = (
    carpeta_script.parents[1] / "Practica 2" / "doc" / "resultados"
    / "5 - Estabilidad y evolucion individual de los equipos.xlsx"
)
carpeta_resultados = carpeta_practica / "doc" / "resultados"
carpeta_graficas = carpeta_practica / "doc" / "Graficas"
carpeta_resultados.mkdir(parents=True, exist_ok=True)
carpeta_graficas.mkdir(parents=True, exist_ok=True)


# CONFIGURACION
PARTIDOS_TEMPORADA = 38
ALFA = 0.05
VARIABLES = ["GF/PJ", "GC/PJ", "Puntos/PJ"]

# CARGAR Y PREPARAR DATOS
def cargar_datos():
    if not archivo_excel.exists():
        raise FileNotFoundError("No se encontró el archivo de resultados de la Práctica 2:\n"
            f"{archivo_excel} Se recomienda usar la estructura original de carpetas.")

    df = pd.read_excel(archivo_excel, sheet_name="Evolución por temporada")
    columnas = ["Temporada", "Equipo", "Posición", "Puntos", "Goles a favor", "Goles en contra"]
    df = df[columnas].copy()

    if df[columnas].isnull().any().any():
        raise ValueError("Hay valores faltantes en las columnas necesarias.")
    if df.duplicated(["Temporada", "Equipo"]).any():
        raise ValueError("Hay registros duplicados por temporada y equipo.")

    df["GF/PJ"] = df["Goles a favor"] / PARTIDOS_TEMPORADA
    df["GC/PJ"] = df["Goles en contra"] / PARTIDOS_TEMPORADA
    df["DG/PJ"] = (df["Goles a favor"] - df["Goles en contra"]) / PARTIDOS_TEMPORADA
    df["Puntos/PJ"] = df["Puntos"] / PARTIDOS_TEMPORADA
    df["Grupo"] = pd.cut(
        df["Posición"], bins=[0, 5, 10, 15, 20],
        labels=["1.º-5.º", "6.º-10.º", "11.º-15.º", "16.º-20.º"],
        include_lowest=True
    ).astype(str)

    if len(df) != 300:
        print(f"Solo para avisar, esperabamos 300 registros; se encontraron {len(df)}.")
    return df


# AJUSTE DE REGRESION LINEAL POR MINIMOS CUADRADOS
def ajustar_modelo(df, nombre, predictores):
    y = df["Puntos/PJ"].to_numpy(dtype=float)
    valores_x = df[predictores].to_numpy(dtype=float)
    x = np.column_stack([np.ones(len(df)), valores_x])
    n, k = x.shape

    beta = np.linalg.lstsq(x, y, rcond=None)[0]
    estimados = x @ beta
    residuos = y - estimados
    sse = float(np.sum(residuos ** 2))
    sst = float(np.sum((y - y.mean()) ** 2))
    r2 = 1 - sse / sst if sst else np.nan
    r2_ajustado = 1 - (1 - r2) * (n - 1) / (n - k) if n > k else np.nan
    gl_residuales = n - k
    mse = sse / gl_residuales
    covarianza = mse * np.linalg.inv(x.T @ x)
    errores = np.sqrt(np.diag(covarianza))
    t_valores = beta / errores
    p_valores = 2 * stats.t.sf(np.abs(t_valores), df=gl_residuales)
    t_critico = stats.t.ppf(1 - ALFA / 2, df=gl_residuales)
    f_estadistico = ((sst - sse) / (k - 1)) / mse if k > 1 and mse > 0 else np.nan
    p_modelo = stats.f.sf(f_estadistico, k - 1, gl_residuales) if np.isfinite(f_estadistico) else np.nan

    coeficientes = [{
        "Modelo": nombre, "Término": "Intercepto", "Coeficiente": beta[0],
        "Error estándar": errores[0], "t": t_valores[0], "p-valor": p_valores[0],
        "IC 95% inferior": beta[0] - t_critico * errores[0],
        "IC 95% superior": beta[0] + t_critico * errores[0]
    }]
    for i, variable in enumerate(predictores, start=1):
        coeficientes.append({
            "Modelo": nombre, "Término": variable, "Coeficiente": beta[i],
            "Error estándar": errores[i], "t": t_valores[i], "p-valor": p_valores[i],
            "IC 95% inferior": beta[i] - t_critico * errores[i],
            "IC 95% superior": beta[i] + t_critico * errores[i]
        })

    resumen = {
        "Modelo": nombre, "Variable objetivo": "Puntos/PJ",
        "Predictores": " + ".join(predictores), "n": n,
        "R²": r2, "R² ajustado": r2_ajustado,
        "F del modelo": f_estadistico, "p-valor del modelo": p_modelo,
        "Error cuadrático medio residual": mse
    }
    predicciones = df[["Temporada", "Equipo", "Posición", "Grupo", "Puntos/PJ"]].copy()
    predicciones["Modelo"] = nombre
    predicciones["Puntos/PJ estimados"] = estimados
    predicciones["Residuo"] = residuos
    return resumen, coeficientes, predicciones


def correlaciones(df):
    filas = []
    pares = [("GF/PJ", "Puntos/PJ"), ("GC/PJ", "Puntos/PJ"), ("GF/PJ", "GC/PJ")]
    for variable_x, variable_y in pares:
        r, p = stats.pearsonr(df[variable_x], df[variable_y])
        filas.append({"Variable X": variable_x, "Variable Y": variable_y,
                      "Correlación (r)": r, "p-valor": p, "n": len(df)})
    return pd.DataFrame(filas)

def resumen_perfiles(df):
    columnas = ["GF/PJ", "GC/PJ", "DG/PJ", "Puntos/PJ"]
    resumen = df.groupby("Grupo", observed=True)[columnas].agg(["count", "mean", "median", "std"])
    resumen.columns = [f"{variable} - {estadistico}" for variable, estadistico in resumen.columns]
    resumen = resumen.reset_index()

    extremos = df[df["Posición"].eq(1) | df["Posición"].between(18, 20)].copy()
    extremos["Extremo"] = np.where(extremos["Posición"].eq(1), "Campeón (1.º)", "Últimos tres (18.º-20.º)")
    comparacion = extremos.groupby("Extremo", observed=True)[columnas].agg(["count", "mean", "median", "std"])
    comparacion.columns = [f"{variable} - {estadistico}" for variable, estadistico in comparacion.columns]
    return resumen, comparacion.reset_index()

# GRAFICAS
def guardar_dispersion(df, x, y, titulo, etiqueta_x, etiqueta_y, archivo):
    plt.figure(figsize=(10, 6))
    for grupo, datos in df.groupby("Grupo", observed=True):
        plt.scatter(datos[x], datos[y], alpha=0.75, s=38, label=grupo)

    ajuste = stats.linregress(df[x], df[y])
    x_linea = np.linspace(df[x].min(), df[x].max(), 100)
    plt.plot(x_linea, ajuste.intercept + ajuste.slope * x_linea,
             label=f"Regresión lineal (R² = {ajuste.rvalue ** 2:.3f})")
    plt.xlabel(etiqueta_x)
    plt.ylabel(etiqueta_y)
    plt.title(titulo)
    plt.legend(title="Posición final")
    plt.grid(True, alpha=0.25)
    plt.tight_layout()
    plt.savefig(carpeta_graficas / archivo, dpi=300, bbox_inches="tight")
    plt.close()

def guardar_reales_estimados(predicciones, r2):
    plt.figure(figsize=(8, 7))
    for grupo, datos in predicciones.groupby("Grupo", observed=True):
        plt.scatter(datos["Puntos/PJ"], datos["Puntos/PJ estimados"],
                    alpha=0.75, s=38, label=grupo)

    minimo = min(predicciones["Puntos/PJ"].min(), predicciones["Puntos/PJ estimados"].min())
    maximo = max(predicciones["Puntos/PJ"].max(), predicciones["Puntos/PJ estimados"].max())
    plt.plot([minimo, maximo], [minimo, maximo], linestyle="--", label="Estimación perfecta")
    plt.xlabel("Puntos reales por partido")
    plt.ylabel("Puntos estimados por partido")
    plt.title(f"Puntos reales frente a estimados: modelo conjunto (R² = {r2:.3f})")
    plt.legend(title="Posición final")
    plt.grid(True, alpha=0.25)
    plt.tight_layout()
    plt.savefig(carpeta_graficas / "03_reales_vs_estimados.png", dpi=300, bbox_inches="tight")
    plt.close()

def guardar_residuos(predicciones):
    plt.figure(figsize=(10, 6))
    plt.scatter(predicciones["Puntos/PJ estimados"], predicciones["Residuo"], alpha=0.75, s=38)
    plt.axhline(0, linestyle="--")
    plt.xlabel("Puntos estimados por partido")
    plt.ylabel("Residuo (real - estimado)")
    plt.title("Diagnóstico de residuos del modelo conjunto")
    plt.grid(True, alpha=0.25)
    plt.tight_layout()
    plt.savefig(carpeta_graficas / "04_diagnostico_residuos.png", dpi=300, bbox_inches="tight")
    plt.close()


def main():
    df = cargar_datos()
    modelos = [
        ("Modelo 1 - Ofensivo", ["GF/PJ"]),
        ("Modelo 2 - Defensivo", ["GC/PJ"]),
        ("Modelo 3 - Conjunto", ["GF/PJ", "GC/PJ"])]
    
    resumen_modelos, coeficientes, predicciones_modelo = [], [], {}

    for nombre, predictores in modelos:
        resumen, coef, pred = ajustar_modelo(df, nombre, predictores)
        resumen_modelos.append(resumen)
        coeficientes.extend(coef)
        predicciones_modelo[nombre] = pred

    tabla_modelos = pd.DataFrame(resumen_modelos)
    tabla_coeficientes = pd.DataFrame(coeficientes)
    tabla_correlaciones = correlaciones(df)
    perfiles, extremos = resumen_perfiles(df)
    predicciones = predicciones_modelo["Modelo 3 - Conjunto"]

    guardar_dispersion(
        df, "GF/PJ", "Puntos/PJ",
        "Relación entre producción ofensiva y puntos", "Goles a favor por partido",
        "Puntos por partido", "01_goles_a_favor_vs_puntos.png"
    )
    guardar_dispersion(
        df, "GC/PJ", "Puntos/PJ",
        "Relación entre goles recibidos y puntos", "Goles en contra por partido",
        "Puntos por partido", "02_goles_en_contra_vs_puntos.png"
    )

    r2_conjunto = tabla_modelos.loc[tabla_modelos["Modelo"] == "Modelo 3 - Conjunto", "R²"].iloc[0]
    guardar_reales_estimados(predicciones, r2_conjunto)
    guardar_residuos(predicciones)

    with pd.ExcelWriter(carpeta_resultados / "resultados_practica5.xlsx") as escritor:
        tabla_modelos.to_excel(escritor, sheet_name="Comparación de modelos", index=False)
        tabla_coeficientes.to_excel(escritor, sheet_name="Coeficientes", index=False)
        tabla_correlaciones.to_excel(escritor, sheet_name="Correlaciones", index=False)
        perfiles.to_excel(escritor, sheet_name="Perfiles por zona", index=False)
        extremos.to_excel(escritor, sheet_name="Campeón vs últimos tres", index=False)
        predicciones.to_excel(escritor, sheet_name="Estimaciones y residuos", index=False)
        df.to_excel(escritor, sheet_name="Datos analizados", index=False)

    print("\nPRACTICA 5 - MODELOS LINEALES Y CORRELACION")
    print(tabla_modelos[["Modelo", "R²", "R² ajustado", "F del modelo", "p-valor del modelo"]].to_string(index=False))
    print(f"\nResultados: {carpeta_resultados / 'resultados_practica5.xlsx'}")
    print(f"Graficas: {carpeta_graficas}")

if __name__ == "__main__":
    main()
