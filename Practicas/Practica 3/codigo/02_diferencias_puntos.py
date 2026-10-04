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
    / "2 - Diferencias de puntos por posicion.xlsx"
)

carpeta_salida = (
    carpeta_script.parent
    / "doc"
    / "Graficas"
    / "02 - Diferencias de puntos por posicion"
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


# GRAFICAR DIFERENCIAS

def graficar_diferencias(df):

    plt.figure(figsize=(11, 6))

    datos = [
        df["1.º - 2.º"],
        df["5.º - 6.º"],
        df["10.º - 11.º"],
        df["19.º - 20.º"]
    ]

    plt.boxplot(
        datos,
        tick_labels=[
            "1.º - 2.º",
            "5.º - 6.º",
            "10.º - 11.º",
            "19.º - 20.º"
        ]
    )

    plt.xlabel("Comparación de posiciones")
    plt.ylabel("Diferencia de puntos")

    plt.title(
        "Distribución de las diferencias de puntos según posición"
    )

    plt.grid(
        True,
        axis="y",
        alpha=0.25
    )

    plt.tight_layout()

    ruta_grafica = (
        carpeta_salida
        / "02_distribucion_diferencias_puntos.png"
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

    graficar_diferencias(
        df
    )


if __name__ == "__main__":
    main()