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
    / "3 - Concentracion y estabilidad parte alta.xlsx"
)

carpeta_salida = (
    carpeta_script.parent
    / "doc"
    / "Graficas"
    / "03 - Concentracion y estabilidad parte alta"
)


carpeta_salida.mkdir(
    parents=True,
    exist_ok=True
)


# CARGAR DATOS

def cargar_datos():

    df = pd.read_excel(
        archivo_excel,
        sheet_name="Apariciones Top 5"
    )

    return df


# GRAFICAR APARICIONES

def graficar_apariciones(df):

    df = df.sort_values(
        "Apariciones Top 5",
        ascending=True
    )

    plt.figure(figsize=(11, 6))

    plt.barh(
        df["Equipo"],
        df["Apariciones Top 5"]
    )

    plt.xlabel("Número de temporadas")
    plt.ylabel("Equipo")

    plt.title(
        "Apariciones de los equipos en el Top 5"
    )

    plt.grid(
        True,
        axis="x",
        alpha=0.25
    )

    plt.tight_layout()

    ruta_grafica = (
        carpeta_salida
        / "03_apariciones_top_5.png"
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

    graficar_apariciones(
        df
    )


if __name__ == "__main__":
    main()