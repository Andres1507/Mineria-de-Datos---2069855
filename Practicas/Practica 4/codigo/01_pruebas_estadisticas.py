from pathlib import Path
from itertools import combinations

import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats


# RUTAS
carpeta_script = Path(__file__).resolve().parent
archivo_excel = (
    carpeta_script.parents[1] / "Practica 2" / "doc" / "resultados"
    / "5 - Estabilidad y evolucion individual de los equipos.xlsx"
)
carpeta_practica = carpeta_script.parent
carpeta_resultados = carpeta_practica / "doc" / "resultados"
carpeta_graficas = carpeta_practica / "doc" / "Graficas"

nombres_analisis = {
    "01_ofensivo": "Analisis 1 - Ofensivo",
    "02_defensivo": "Analisis 2 - Defensivo",
    "03_diferencia_goles": "Analisis 3 - Diferencia de goles",
    "04_competitividad": "Analisis 4 - Competitividad",
}
carpetas_resultados = {
    clave: carpeta_resultados / nombre for clave, nombre in nombres_analisis.items()
}
carpetas_graficas = {
    clave: carpeta_graficas / nombre for clave, nombre in nombres_analisis.items()
}
for carpeta in [carpeta_resultados, carpeta_graficas,
                *carpetas_resultados.values(), *carpetas_graficas.values()]:
    carpeta.mkdir(parents=True, exist_ok=True)


# CONFIGURACION
PARTIDOS_TEMPORADA = 38
ALFA = 0.05
ZONAS = ["1.º-5.º", "6.º-10.º", "11.º-15.º", "16.º-20.º"]


# CARGAR DATOS
def cargar_datos():
    if not archivo_excel.exists():
        raise FileNotFoundError(
            "No se encontró el archivo de resultados de la Práctica 2:\n"
            f"{archivo_excel}\nConserva la estructura original de carpetas."
        )

    df = pd.read_excel(archivo_excel, sheet_name="Evolución por temporada")
    columnas = ["Temporada", "Equipo", "Posición", "Puntos", "Goles a favor", "Goles en contra"]
    df = df[columnas].copy()
    if df[columnas].isnull().any().any():
        raise ValueError("Hay valores faltantes en las columnas necesarias.")

    df["GF/PJ"] = df["Goles a favor"] / PARTIDOS_TEMPORADA
    df["GC/PJ"] = df["Goles en contra"] / PARTIDOS_TEMPORADA
    df["DG/PJ"] = (df["Goles a favor"] - df["Goles en contra"]) / PARTIDOS_TEMPORADA
    df["Puntos/PJ"] = df["Puntos"] / PARTIDOS_TEMPORADA
    df["Zona"] = pd.cut(
        df["Posición"], bins=[0, 5, 10, 15, 20], labels=ZONAS,
        include_lowest=True
    ).astype(str)
    df = df.dropna(subset=["Zona", "GF/PJ", "GC/PJ", "DG/PJ", "Puntos/PJ"])
    if len(df) != 300:
        print(f"AVISO: se esperaban 300 registros equipo-temporada; se encontraron {len(df)}.")
    return df



def descriptivos_zona(df, variable, nombre):
    filas = []
    for zona in ZONAS:
        valores = df.loc[df["Zona"] == zona, variable]
        filas.append({
            "Zona": zona, "Observaciones": len(valores),
            f"Media {nombre}": valores.mean(), f"Mediana {nombre}": valores.median(),
            f"Desv. estándar {nombre}": valores.std(ddof=1),
            f"Q1 {nombre}": valores.quantile(0.25), f"Q3 {nombre}": valores.quantile(0.75),
            f"RIC {nombre}": valores.quantile(0.75) - valores.quantile(0.25),
            f"Mínimo {nombre}": valores.min(), f"Máximo {nombre}": valores.max()
        })
    return pd.DataFrame(filas)


def ajustar_holm(p_values):
    p_values = list(p_values)
    m = len(p_values)
    orden = sorted(range(m), key=lambda i: p_values[i])
    ajustados = [0.0] * m
    max_previo = 0.0
    for rango, indice in enumerate(orden):
        valor = min(1.0, (m - rango) * p_values[indice])
        max_previo = max(max_previo, valor)
        ajustados[indice] = max_previo
    return ajustados


def prueba_kruskal(df, variable, nombre):
    grupos = [df.loc[df["Zona"] == zona, variable].to_numpy() for zona in ZONAS]
    prueba = stats.kruskal(*grupos)
    n = len(df)
    k = len(grupos)
    epsilon2 = max(0, (prueba.statistic - k + 1) / (n - k)) if n > k else float("nan")

    filas = []
    for zona in ZONAS:
        valores = df.loc[df["Zona"] == zona, variable]
        filas.append({"Zona": zona, "n": len(valores), "Media": valores.mean(),
                      "Mediana": valores.median(), "Desv. estándar": valores.std(ddof=1),
                      "Q1": valores.quantile(.25), "Q3": valores.quantile(.75),
                      "RIC": valores.quantile(.75) - valores.quantile(.25)})
    descriptivos = pd.DataFrame(filas)


    # DUNN CON CORRECCION POR EMPATES
    datos = df[["Zona", variable]].copy()
    datos["Rango"] = stats.rankdata(datos[variable].to_numpy())
    conteos = datos[variable].value_counts().to_numpy()
    correccion_empates = 1 - sum(t**3 - t for t in conteos) / (n**3 - n)
    varianza_base = n * (n + 1) / 12 * correccion_empates
    resumen_rangos = {}
    for zona in ZONAS:
        sub = datos[datos["Zona"] == zona]
        resumen_rangos[zona] = (len(sub), sub["Rango"].mean(), sub[variable].median())

    comparaciones = []
    for zona1, zona2 in combinations(ZONAS, 2):
        n1, rango1, mediana1 = resumen_rangos[zona1]
        n2, rango2, mediana2 = resumen_rangos[zona2]
        error = (varianza_base * (1 / n1 + 1 / n2)) ** .5
        z = (rango1 - rango2) / error
        p = 2 * stats.norm.sf(abs(z))
        comparaciones.append({"Zona 1": zona1, "Zona 2": zona2,
                              f"Mediana {nombre} zona 1": mediana1,
                              f"Mediana {nombre} zona 2": mediana2,
                              "Diferencia rangos medios": rango1 - rango2,
                              "Z Dunn": z, "p sin ajustar": p})
    comparaciones = pd.DataFrame(comparaciones)
    comparaciones["p ajustado Holm"] = ajustar_holm(comparaciones["p sin ajustar"])
    comparaciones["Conclusión"] = comparaciones["p ajustado Holm"].apply(
        lambda p: "Diferencia significativa" if p < ALFA else "Sin diferencia significativa")

    resultado = pd.DataFrame([{
        "Variable": nombre, "Prueba": "Kruskal-Wallis", "H": prueba.statistic,
        "p-value": prueba.pvalue, "Epsilon cuadrada aproximada": epsilon2,
        "Conclusión (alfa=0.05)": "Se rechaza H0" if prueba.pvalue < ALFA else "No se rechaza H0"
    }])
    return descriptivos, resultado, comparaciones


def guardar_boxplot(df, variable, nombre, titulo, archivo, carpeta_destino):
    datos = [df.loc[df["Zona"] == zona, variable].to_numpy() for zona in ZONAS]
    plt.figure(figsize=(10, 6))
    plt.boxplot(datos, tick_labels=ZONAS, showmeans=True)
    plt.xlabel("Zona de clasificación")
    plt.ylabel(nombre)
    plt.title(titulo)
    plt.grid(True, axis="y", alpha=.25)
    plt.tight_layout()
    plt.savefig(carpeta_destino / archivo, dpi=300, bbox_inches="tight")
    plt.close()



def analizar_competitividad(df):
    filas = []
    for (temporada, zona), grupo in df.groupby(["Temporada", "Zona"], observed=True, sort=True):
        puntos = grupo["Puntos"]
        filas.append({
            "Temporada": temporada, "Zona": zona, "Equipos": len(grupo),
            "Media puntos": puntos.mean(), "Mediana puntos": puntos.median(),
            "Desv. estándar puntos": puntos.std(ddof=1),
            "Q1 puntos": puntos.quantile(.25), "Q3 puntos": puntos.quantile(.75),
            "RIC puntos": puntos.quantile(.75) - puntos.quantile(.25),
            "Rango puntos": puntos.max() - puntos.min(),
            "Mínimo puntos": puntos.min(), "Máximo puntos": puntos.max()
        })
    temporada_zona = pd.DataFrame(filas)
    resumen = temporada_zona.groupby("Zona", observed=True).agg(
        Temporadas=("Temporada", "nunique"),
        media_desv_estandar=("Desv. estándar puntos", "mean"),
        mediana_desv_estandar=("Desv. estándar puntos", "median"),
        media_RIC=("RIC puntos", "mean"),
        mediana_RIC=("RIC puntos", "median"),
        media_rango=("Rango puntos", "mean")
    ).reset_index().rename(columns={
        "media_desv_estandar": "Media desviación estándar",
        "mediana_desv_estandar": "Mediana desviación estándar",
        "media_RIC": "Media RIC", "mediana_RIC": "Mediana RIC",
        "media_rango": "Media rango"
    })

    plt.figure(figsize=(11, 6))
    for zona in ZONAS:
        sub = temporada_zona[temporada_zona["Zona"] == zona]
        plt.plot(sub["Temporada"], sub["Desv. estándar puntos"], marker="o", label=zona)
    plt.xlabel("Temporada")
    plt.ylabel("Desviación estándar de puntos")
    plt.title("Evolución de la dispersión de puntos dentro de cada zona")
    plt.xticks(rotation=45, ha="right")
    plt.legend(title="Zona")
    plt.grid(True, axis="y", alpha=.25)
    plt.tight_layout()
    plt.savefig(carpetas_graficas["04_competitividad"] / "04_competitividad_zonas.png", dpi=300, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(10, 6))
    datos = [temporada_zona.loc[temporada_zona["Zona"] == zona, "Desv. estándar puntos"].to_numpy()
             for zona in ZONAS]
    plt.boxplot(datos, tick_labels=ZONAS, showmeans=True)
    plt.xlabel("Zona de clasificación")
    plt.ylabel("Desviación estándar de puntos por temporada")
    plt.title("Comparación de la dispersión de puntos entre temporadas")
    plt.grid(True, axis="y", alpha=.25)
    plt.tight_layout()
    plt.savefig(carpetas_graficas["04_competitividad"] / "04_2_distribucion_competitividad.png", dpi=300, bbox_inches="tight")
    plt.close()
    return temporada_zona, resumen


# EXPORTAR RESULTADOS
def main():
    df = cargar_datos()
    configuraciones = [
        ("GF/PJ", "goles a favor por partido", "01_rendimiento_ofensivo.png",
         "Distribución del rendimiento ofensivo por zona", "01_ofensivo"),
        ("GC/PJ", "goles en contra por partido", "02_rendimiento_defensivo.png",
         "Distribución del rendimiento defensivo por zona", "02_defensivo"),
        ("DG/PJ", "diferencia de goles por partido", "03_diferencia_goles.png",
         "Distribución de la diferencia de goles por zona", "03_diferencia_goles")
    ]
    resumenes = []
    rutas_excel = []

    # EXPORTAR CADA PRUEBA EN LA CARPETA DE SU ANALISIS
    for variable, nombre, grafica, titulo, prefijo in configuraciones:
        descriptivos, prueba, comparaciones = prueba_kruskal(df, variable, nombre)
        ruta_excel = carpetas_resultados[prefijo] / f"resultados_{prefijo}.xlsx"
        with pd.ExcelWriter(ruta_excel) as writer:
            df.to_excel(writer, sheet_name="Datos analizados", index=False)
            descriptivos.to_excel(writer, sheet_name="Descriptivos", index=False)
            prueba.to_excel(writer, sheet_name="Kruskal-Wallis", index=False)
            comparaciones.to_excel(writer, sheet_name="Dunn-Holm", index=False)
        guardar_boxplot(df, variable, nombre, titulo, grafica, carpetas_graficas[prefijo])
        resumenes.append((nombre, descriptivos, prueba, comparaciones))
        rutas_excel.append(ruta_excel)

    temporada_zona, resumen_comp = analizar_competitividad(df)
    ruta_excel_comp = carpetas_resultados["04_competitividad"] / "resultados_04_competitividad.xlsx"
    with pd.ExcelWriter(ruta_excel_comp) as writer:
        temporada_zona.to_excel(writer, sheet_name="Por temporada y zona", index=False)
        resumen_comp.to_excel(writer, sheet_name="Resumen por zona", index=False)
    rutas_excel.append(ruta_excel_comp)

    # RESUMEN GENERAL EN LA CARPETA RAIZ DE RESULTADOS
    ruta_txt = carpeta_resultados / "resumen_general.txt"
    with open(ruta_txt, "w", encoding="utf-8") as archivo:
        archivo.write("PRACTICA 4 - PRUEBAS ESTADISTICAS Y COMPETITIVIDAD EN LALIGA\n")
        archivo.write("=" * 72 + "\n")
        archivo.write(f"Registros equipo-temporada: {len(df)}\nNivel de significancia: {ALFA}\n")
        archivo.write("Zonas: 1.º-5.º, 6.º-10.º, 11.º-15.º y 16.º-20.º\n")
        for nombre, descriptivos, prueba, comparaciones in resumenes:
            archivo.write("\n\n" + "=" * 72 + f"\nANALISIS: {nombre.upper()}\n" + "=" * 72 + "\n")
            archivo.write("\nDESCRIPTIVOS\n" + descriptivos.round(4).to_string(index=False))
            archivo.write("\n\nKRUSKAL-WALLIS\n" + prueba.to_string(
                index=False,
                formatters={"H": lambda x: f"{x:.4f}",
                            "p-value": lambda x: f"{x:.3e}",
                            "Epsilon cuadrada aproximada": lambda x: f"{x:.4f}"}
            ))
            archivo.write("\n\nDUNN CON CORRECCION DE HOLM\n" + comparaciones.to_string(
                index=False,
                formatters={"p sin ajustar": lambda x: f"{x:.3e}",
                            "p ajustado Holm": lambda x: f"{x:.3e}",
                            "Z Dunn": lambda x: f"{x:.4f}",
                            "Diferencia rangos medios": lambda x: f"{x:.4f}"}
            ))
        archivo.write("\n\n" + "=" * 72 + "\nANALISIS 4: COMPETITIVIDAD DENTRO DE LAS ZONAS\n")
        archivo.write("Se describe la dispersión de puntos por zona y temporada mediante desviación estándar, rango intercuartílico y rango. No se aplica una prueba inferencial automáticamente porque el objetivo es estudiar la variabilidad y su evolución temporal.\n")
        archivo.write("\nRESUMEN DE DISPERSION POR ZONA\n" + resumen_comp.round(4).to_string(index=False))
        archivo.write("\n\nLIMITACIONES METODOLOGICAS\n")
        archivo.write("Kruskal-Wallis compara rangos y requiere independencia entre observaciones. Algunos clubes aparecen en varias temporadas, por lo que esa independencia puede no cumplirse completamente; los resultados inferenciales deben interpretarse como exploratorios.\n")
        archivo.write("Las comparaciones de Dunn identifican diferencias en rangos, no necesariamente diferencias de medias.\n")
        archivo.write("El análisis de competitividad mide la dispersión de puntos finales dentro de cada zona; no mide directamente la incertidumbre de los partidos ni demuestra qué tan disputada fue la clasificación durante la temporada.\n")
        archivo.write("Las zonas son agrupaciones analíticas. Las referencias a puestos europeos son orientativas y no confirman clasificación efectiva, que depende de las reglas de cada temporada y de la Copa del Rey.\n")
        archivo.write("Los resultados muestran asociaciones y patrones descriptivos; no demuestran causalidad.\n")

    print("\nPRACTICA 4 COMPLETADA\n")
    print(f"Registros analizados: {len(df)}")
    for nombre, _, prueba, _ in resumenes:
        print(f"{nombre}: H={prueba.iloc[0]['H']:.4f}, p={prueba.iloc[0]['p-value']:.6e}")

    print("\nListo!\n")

    """
    print("Archivos Excel:")
    for ruta in rutas_excel:
        print(f"- {ruta}")
    print(f"Resumen general: {ruta_txt}")
    print(f"Resultados por análisis: {carpeta_resultados}")
    print(f"Gráficas por análisis: {carpeta_graficas}")
    """


if __name__ == "__main__":
    main()
