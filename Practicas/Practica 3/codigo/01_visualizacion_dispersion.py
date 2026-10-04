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
    / "1 - Dispersion y distribucion de puntos.xlsx"
)

carpeta_salida = (
    carpeta_script.parent
    / "doc"
    / "Graficas"
    / "01 - Dispersion y distribucion de puntos"
)


carpeta_salida.mkdir(
    parents=True,
    exist_ok=True
)


# CARGAR DATOS

def cargar_datos():

    df = pd.read_excel(
        archivo_excel
    )

    return df


# GRAFICAR DISPERSION

def graficar_dispersion(df):

    plt.figure(figsize=(11, 6))

    plt.plot(
        df["Temporada"],
        df["Desv. estándar"],
        marker="o",
        label="Desviación estándar"
    )

    plt.plot(
        df["Temporada"],
        df["Rango"],
        marker="o",
        label="Rango"
    )

    plt.xlabel("Temporada")
    plt.ylabel("Puntos")

    plt.title(
        "Evolución de la dispersión de puntos por temporada"
    )

    plt.xticks(rotation=45)

    plt.grid(
        True,
        alpha=0.25
    )

    plt.legend()
    plt.tight_layout()

    ruta_grafica = (
        carpeta_salida
        / "01_evolucion_dispersion.png"
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

    graficar_dispersion(
        df
    )


if __name__ == "__main__":
    main()