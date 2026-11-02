
from pathlib import Path

import pandas as pd


# RUTAS

carpeta_script = Path(__file__).resolve().parent
carpeta_practica = carpeta_script.parent

archivo_excel = (
    carpeta_script.parents[1] / "Practica 2" / "doc" / "resultados"
    / "5 - Estabilidad y evolucion individual de los equipos.xlsx"
)

carpeta_resultados = carpeta_practica / "doc" / "resultados"
carpeta_resultados.mkdir(parents=True, exist_ok=True)

archivo_salida = carpeta_resultados / "01_matriz_perfiles_clubes.xlsx"


# CONFIGURACION

PARTIDOS_TEMPORADA = 38
CLUBES_ESPERADOS = 34

COLUMNAS = [
    "Temporada",
    "Equipo",
    "Posición",
    "Puntos",
    "Goles a favor",
    "Goles en contra"
]

VARIABLES_A = [
    "Posición promedio",
    "GF/PJ",
    "GC/PJ"
]

VARIABLES_B = VARIABLES_A + [
    "% Top 6",
    "% Zona baja"
]


# CARGAR DATOS

def cargar_datos():

    if not archivo_excel.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo:\n{archivo_excel}"
        )

    df = pd.read_excel(
        archivo_excel,
        sheet_name="Evolución por temporada"
    )

    faltantes = [col for col in COLUMNAS if col not in df.columns]

    if faltantes:
        raise ValueError(
            f"Faltan columnas necesarias: {faltantes}"
        )

    df = df[COLUMNAS].copy()

    for col in COLUMNAS[2:]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if df[COLUMNAS].isnull().any().any():
        raise ValueError(
            "Se encontraron valores faltantes o no numéricos."
        )

    if df.duplicated(["Temporada", "Equipo"]).any():
        raise ValueError(
            "Se encontraron registros duplicados por equipo y temporada."
        )

    if not df["Posición"].between(1, 20).all():
        raise ValueError(
            "Se encontraron posiciones fuera del rango de 1 a 20."
        )

    if not df["Goles a favor"].ge(0).all() or not df["Goles en contra"].ge(0).all():
        raise ValueError(
            "Se encontraron valores negativos en los goles."
        )

    if not df["Puntos"].ge(0).all():
        raise ValueError(
            "Se encontraron valores negativos en los puntos."
        )

    return df


# CALCULAR METRICAS POR TEMPORADA

def calcular_metricas(df):

    df["GF/PJ"] = df["Goles a favor"] / PARTIDOS_TEMPORADA
    df["GC/PJ"] = df["Goles en contra"] / PARTIDOS_TEMPORADA
    df["Puntos/PJ"] = df["Puntos"] / PARTIDOS_TEMPORADA

    df["Top 4"] = (df["Posición"] <= 4).astype(int)
    df["Top 6"] = (df["Posición"] <= 6).astype(int)

    df["Zona baja"] = (df["Posición"] >= 16).astype(int)
    df["Zona descenso"] = (df["Posición"] >= 18).astype(int)
    df["Posición 17"] = (df["Posición"] == 17).astype(int)

    return df


# CONSTRUIR PERFILES HISTORICOS

def construir_perfiles(df):

    perfiles = df.groupby("Equipo").agg(
        **{
            "Temporadas participadas": ("Temporada", "nunique"),
            "Posición promedio": ("Posición", "mean"),
            "Mejor posición": ("Posición", "min"),
            "Peor posición": ("Posición", "max"),
            "Desv. posición": ("Posición", "std"),
            "Puntos/PJ": ("Puntos/PJ", "mean"),
            "GF/PJ": ("GF/PJ", "mean"),
            "GC/PJ": ("GC/PJ", "mean"),
            "% Top 4": ("Top 4", "mean"),
            "% Top 6": ("Top 6", "mean"),
            "% Zona baja": ("Zona baja", "mean"),
            "% Zona descenso": ("Zona descenso", "mean"),
            "% Posición 17": ("Posición 17", "mean")
        }
    ).reset_index()

    # CONVERTIR FRECUENCIAS A PORCENTAJES

    columnas_porcentaje = [
        "% Top 4",
        "% Top 6",
        "% Zona baja",
        "% Zona descenso",
        "% Posición 17"
    ]

    perfiles[columnas_porcentaje] *= 100

    return perfiles


# CONSTRUIR MATRICES DE MODELOS

def construir_matrices(perfiles):

    matriz_A = perfiles[
        ["Equipo"] + VARIABLES_A
    ].copy()

    matriz_B = perfiles[
        ["Equipo"] + VARIABLES_B
    ].copy()

    return matriz_A, matriz_B


# DIAGNOSTICO DE DATOS

def diagnosticar_datos(df, perfiles):

    diagnostico = pd.DataFrame({
        "Indicador": [
            "Registros equipo-temporada",
            "Clubes identificados",
            "Temporadas identificadas",
            "Registros duplicados",
            "Valores faltantes originales",
            "Clubes con una sola participación",
            "Clubes con varias participaciones",
            "Clubes sin desviación calculable"
        ],
        "Resultado": [
            len(df),
            perfiles["Equipo"].nunique(),
            df["Temporada"].nunique(),
            df.duplicated(["Temporada", "Equipo"]).sum(),
            df[COLUMNAS].isnull().sum().sum(),
            (perfiles["Temporadas participadas"] == 1).sum(),
            (perfiles["Temporadas participadas"] > 1).sum(),
            perfiles["Desv. posición"].isna().sum()
        ]
    })

    return diagnostico


# GUARDAR RESULTADOS

def guardar_resultados(
    perfiles,
    matriz_A,
    matriz_B,
    diagnostico
):

    with pd.ExcelWriter(archivo_salida) as writer:

        perfiles.to_excel(
            writer,
            sheet_name="Perfiles históricos",
            index=False
        )

        matriz_A.to_excel(
            writer,
            sheet_name="Modelo A",
            index=False
        )

        matriz_B.to_excel(
            writer,
            sheet_name="Modelo B",
            index=False
        )

        diagnostico.to_excel(
            writer,
            sheet_name="Diagnóstico",
            index=False
        )


# EJECUCION PRINCIPAL

def main():

    print("\nPREPARACION DE DATOS - PRACTICA 7\n")

    df = cargar_datos()

    print(f"Registros cargados: {len(df)}")

    df = calcular_metricas(df)

    perfiles = construir_perfiles(df)

    matriz_A, matriz_B = construir_matrices(perfiles)

    diagnostico = diagnosticar_datos(df, perfiles)

    if len(perfiles) != CLUBES_ESPERADOS:
        print(
            f"\nAVISO: Se esperaban {CLUBES_ESPERADOS} clubes "
            f"y se encontraron {len(perfiles)}."
        )

    guardar_resultados(
        perfiles,
        matriz_A,
        matriz_B,
        diagnostico
    )

    print("\nRESUMEN")
    print(f"Clubes identificados: {len(perfiles)}")
    print(f"Variables Modelo A: {len(VARIABLES_A)}")
    print(f"Variables Modelo B: {len(VARIABLES_B)}")

    print("\nDIAGNOSTICO")
    print(diagnostico.to_string(index=False))

    print("\nRESULTADOS GUARDADOS EN:")
    print(archivo_salida)


if __name__ == "__main__":
    main()
