from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# RUTAS

carpeta_script = Path(__file__).resolve().parent

archivo_excel = (
    carpeta_script.parents[1]
    / "02 Estadistica Descriptiva"
    / "doc"
    / "resultados"
    / "4 - Movilidad entre zonas de la clasificacion.xlsx"
)

carpeta_salida = (
    carpeta_script.parent
    / "doc"
    / "Graficas"
    / "04 - Movilidad entre zonas"
)

carpeta_salida.mkdir(
    parents=True,
    exist_ok=True
)


# CARGAR DATOS

def cargar_datos():

    df_movilidad = pd.read_excel(
        archivo_excel,
        sheet_name="Movilidad general"
    )

    df_destacados = pd.read_excel(
        archivo_excel,
        sheet_name="Movimientos destacados"
    )

    return df_movilidad, df_destacados


# GRAFICAR MOVILIDAD GENERAL

def graficar_movilidad(df):

    plt.figure(figsize=(12, 6))

    plt.bar(
        df["Temporada"],
        df["Misma zona"],
        label="Misma zona"
    )

    plt.bar(
        df["Temporada"],
        df["Suben de zona"],
        bottom=df["Misma zona"],
        label="Suben de zona"
    )

    plt.bar(
        df["Temporada"],
        df["Bajan de zona"],
        bottom=(
            df["Misma zona"]
            + df["Suben de zona"]
        ),
        label="Bajan de zona"
    )

    plt.xlabel("Temporada")
    plt.ylabel("Número de equipos")

    plt.title(
        "Movilidad de los equipos entre zonas de la clasificación"
    )

    plt.xticks(
        rotation=45
    )

    plt.grid(
        True,
        axis="y",
        alpha=0.25
    )

    plt.legend()

    plt.tight_layout()

    ruta_grafica = (
        carpeta_salida
        / "04_movilidad_entre_zonas.png"
    )

    plt.savefig(
        ruta_grafica,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    print(
        f"Gráfica guardada en: {ruta_grafica}"
    )


# GRAFICAR MOVIMIENTOS DESTACADOS

def graficar_movimientos_destacados(df):

    temporadas = df["Temporada"]

    llegadas_top_10 = df[
        "Llegan Top 10 desde 11-20"
    ].str.split(",").apply(
        lambda equipos: 0 if equipos == [""] else len(equipos)
    )

    llegadas_top_5 = df[
        "Llegan Top 5 desde 6-20"
    ].str.split(",").apply(
        lambda equipos: 0 if equipos == [""] else len(equipos)
    )

    salidas_top_10 = df[
        "Pasan de Top 10 a 11-20"
    ].str.split(",").apply(
        lambda equipos: 0 if equipos == [""] else len(equipos)
    )

    posiciones = range(len(temporadas))
    ancho = 0.25

    plt.figure(figsize=(12, 6))

    plt.bar(
        [posicion - ancho for posicion in posiciones],
        llegadas_top_10,
        width=ancho,
        label="Llegan al Top 10"
    )

    plt.bar(
        posiciones,
        llegadas_top_5,
        width=ancho,
        label="Llegan al Top 5"
    )

    plt.bar(
        [posicion + ancho for posicion in posiciones],
        salidas_top_10,
        width=ancho,
        label="Salen del Top 10"
    )

    plt.xlabel("Temporada")
    plt.ylabel("Número de equipos")

    plt.title(
        "Movimientos destacados entre zonas de la clasificación"
    )

    plt.xticks(
        posiciones,
        temporadas,
        rotation=45
    )

    plt.grid(
        True,
        axis="y",
        alpha=0.25
    )

    plt.legend()

    plt.tight_layout()

    ruta_grafica = (
        carpeta_salida
        / "04_movimientos_destacados.png"
    )

    plt.savefig(
        ruta_grafica,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    print(
        f"Gráfica guardada en: {ruta_grafica}"
    )


# PROCESO PRINCIPAL

def main():

    df_movilidad, df_destacados = cargar_datos()

    graficar_movilidad(
        df_movilidad
    )

    graficar_movimientos_destacados(
        df_destacados
    )


if __name__ == "__main__":
    main()