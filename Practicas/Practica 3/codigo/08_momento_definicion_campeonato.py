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
    / "8 - Momento de Definicion del Campeonato.xlsx"
)

carpeta_salida = (
    carpeta_script.parent
    / "doc"
    / "Graficas"
    / "08 - Momento de definicion matematica"
)

carpeta_salida.mkdir(
    parents=True,
    exist_ok=True
)


# CARGAR DATOS

def cargar_datos():

    df = pd.read_excel(
        archivo_excel,
        sheet_name="Definición campeonato"
    )

    return df


# GRAFICAR PARTIDOS PARA DEFINIR EL CAMPEONATO

def graficar_partidos_definicion(df):

    plt.figure(figsize=(12, 6))

    plt.bar(
        df["Temporada"],
        df["Partidos disputados por el campeón"]
    )

    plt.xlabel("Temporada")
    plt.ylabel("Partidos disputados por el campeón")

    plt.title(
        "Partidos disputados por el campeón al definir el campeonato"
    )

    plt.xticks(
        rotation=45
    )

    plt.grid(
        True,
        axis="y",
        alpha=0.25
    )

    plt.tight_layout()

    ruta_grafica = (
        carpeta_salida
        / "08_partidos_para_definir_campeonato.png"
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


# GRAFICAR DIFERENCIA MINIMA

def graficar_diferencia_minima(df):

    plt.figure(figsize=(12, 6))

    plt.bar(
        df["Temporada"],
        df["Diferencia mínima de puntos"]
    )

    plt.xlabel("Temporada")
    plt.ylabel("Diferencia mínima de puntos")

    plt.title(
        "Diferencia mínima de puntos al definir el campeonato"
    )

    plt.xticks(
        rotation=45
    )

    plt.grid(
        True,
        axis="y",
        alpha=0.25
    )

    plt.tight_layout()

    ruta_grafica = (
        carpeta_salida
        / "08_diferencia_minima_campeonato.png"
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

    df = cargar_datos()

    graficar_partidos_definicion(
        df
    )

    graficar_diferencia_minima(
        df
    )


if __name__ == "__main__":
    main()