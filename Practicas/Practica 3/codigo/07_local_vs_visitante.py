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
    / "7 - Rendimiento Local y Visitante.xlsx"
)

carpeta_salida = (
    carpeta_script.parent
    / "doc"
    / "Graficas"
    / "07 - Rendimiento Local y Visitante"
)

carpeta_salida.mkdir(
    parents=True,
    exist_ok=True
)


# CARGAR DATOS

def cargar_datos():

    df = pd.read_excel(
        archivo_excel,
        sheet_name="Perfil por equipo"
    )

    return df


# GRAFICAR INDICE DE EXITO

def graficar_indice_exito(df):

    df = df.sort_values(
        "Índice de éxito Local",
        ascending=True
    )

    plt.figure(figsize=(11, 10))

    posiciones = range(len(df))

    plt.scatter(
        df["Índice de éxito Visitante"],
        posiciones,
        label="Visitante"
    )

    plt.scatter(
        df["Índice de éxito Local"],
        posiciones,
        label="Local"
    )

    for i, equipo in enumerate(df["Equipo"]):

        plt.plot(
            [
                df.iloc[i]["Índice de éxito Visitante"],
                df.iloc[i]["Índice de éxito Local"]
            ],
            [
                i,
                i
            ],
            alpha=0.4
        )

    plt.yticks(
        list(posiciones),
        df["Equipo"]
    )

    plt.xlabel("Índice de éxito (%)")
    plt.ylabel("Equipo")

    plt.title(
        "Índice de éxito de los equipos como local y visitante"
    )

    plt.grid(
        True,
        axis="x",
        alpha=0.25
    )

    plt.legend()

    plt.tight_layout()

    ruta_grafica = (
        carpeta_salida
        / "01_indice_de_exito_local_vs_visitante.png"
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


# GRAFICAR DIFERENCIA DE GOLES

def graficar_diferencia_goles(df):

    df = df.copy()

    df["Dif. GF/PJ"] = (
        df["GF/PJ Local"]
        - df["GF/PJ Visitante"]
    )

    df = df.sort_values(
        "Dif. GF/PJ",
        ascending=True
    )

    plt.figure(figsize=(11, 10))

    posiciones = range(len(df))

    plt.barh(
        posiciones,
        df["Dif. GF/PJ"]
    )

    plt.yticks(
        list(posiciones),
        df["Equipo"]
    )

    plt.axvline(
        0,
        linewidth=1
    )

    plt.xlabel(
        "Diferencia de goles por partido (Local - Visitante)"
    )

    plt.ylabel("Equipo")

    plt.title(
        "Diferencia de producción ofensiva según condición"
    )

    plt.grid(
        True,
        axis="x",
        alpha=0.25
    )

    plt.tight_layout()

    ruta_grafica = (
        carpeta_salida
        / "02_diferencia_goles_por_partido.png"
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


# GRAFICAR EFECTIVIDAD DE TIRO

def graficar_efectividad_tiro(df):

    df = df.sort_values(
        "Dif. efectividad de tiro",
        ascending=True
    )

    plt.figure(figsize=(11, 10))

    posiciones = range(len(df))

    plt.barh(
        posiciones,
        df["Dif. efectividad de tiro"]
    )

    plt.yticks(
        list(posiciones),
        df["Equipo"]
    )

    plt.axvline(
        0,
        linewidth=1
    )

    plt.xlabel(
        "Diferencia de efectividad de tiro (%) (Local - Visitante)"
    )

    plt.ylabel("Equipo")

    plt.title(
        "Diferencia de efectividad de tiro según condición"
    )

    plt.grid(
        True,
        axis="x",
        alpha=0.25
    )

    plt.tight_layout()

    ruta_grafica = (
        carpeta_salida
        / "03_diferencia_efectividad_tiro.png"
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

    graficar_indice_exito(
        df
    )

    graficar_diferencia_goles(
        df
    )

    graficar_efectividad_tiro(
        df
    )


if __name__ == "__main__":
    main()