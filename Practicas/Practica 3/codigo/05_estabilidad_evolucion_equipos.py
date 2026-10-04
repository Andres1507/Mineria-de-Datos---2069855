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
    / "5 - Estabilidad y evolucion individual de los equipos.xlsx"
)

carpeta_salida = (
    carpeta_script.parent
    / "doc"
    / "Graficas"
    / "05 - Estabilidad y evolucion individual de los equipos"
)

carpeta_salida.mkdir(
    parents=True,
    exist_ok=True
)


# CARGAR DATOS

def cargar_datos():

    df_resumen = pd.read_excel(
        archivo_excel,
        sheet_name="Resumen por equipo"
    )

    df_evolucion = pd.read_excel(
        archivo_excel,
        sheet_name="Evolución por temporada"
    )

    df_cambios = pd.read_excel(
        archivo_excel,
        sheet_name="Cambios de posición"
    )

    return (
        df_resumen,
        df_evolucion,
        df_cambios
    )


# GRAFICAR ESTABILIDAD

def graficar_estabilidad(df):

    plt.figure(figsize=(11, 7))

    plt.scatter(
        df["Posición promedio"],
        df["Desv. estándar posición"]
    )

    for _, fila in df.iterrows():

        plt.annotate(
            fila["Equipo"],
            (
                fila["Posición promedio"],
                fila["Desv. estándar posición"]
            ),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8
        )

    plt.xlabel("Posición promedio")
    plt.ylabel("Desviación estándar de la posición")

    plt.title(
        "Estabilidad de los equipos según su posición promedio"
    )

    plt.gca().invert_xaxis()

    plt.grid(
        True,
        alpha=0.25
    )

    plt.tight_layout()

    ruta_grafica = (
        carpeta_salida
        / "01_estabilidad_equipos.png"
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


# GRAFICAR RANGO DE POSICIONES

def graficar_rango(df):

    df = df[
        df["Temporadas participadas"] >= 10
    ].copy()

    df = df.sort_values(
        "Rango de posiciones",
        ascending=True
    )

    plt.figure(figsize=(11, 7))

    plt.barh(
        df["Equipo"],
        df["Rango de posiciones"]
    )

    plt.xlabel("Rango de posiciones")
    plt.ylabel("Equipo")

    plt.title(
        "Variación de las posiciones de los equipos"
    )

    plt.grid(
        True,
        axis="x",
        alpha=0.25
    )

    plt.tight_layout()

    ruta_grafica = (
        carpeta_salida
        / "02_rango_posiciones_equipos.png"
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


# SELECCIONAR EQUIPOS REPRESENTATIVOS

def seleccionar_equipos(df):

    df = df[
        df["Temporadas participadas"] >= 10
    ].copy()

    equipos_estables = (
        df.sort_values(
            "Desv. estándar posición"
        )
        .head(3)["Equipo"]
        .tolist()
    )

    equipos_variables = (
        df.sort_values(
            "Desv. estándar posición",
            ascending=False
        )
        .head(2)["Equipo"]
        .tolist()
    )

    equipos = (
        equipos_estables
        + equipos_variables
    )

    return equipos


# GRAFICAR EVOLUCIÓN DE POSICIONES

def graficar_evolucion(df_resumen, df_evolucion):

    equipos = seleccionar_equipos(
        df_resumen
    )

    df = df_evolucion[
        df_evolucion["Equipo"].isin(equipos)
    ].copy()

    df = df.sort_values(
        "Temporada"
    )

    plt.figure(figsize=(12, 7))

    for equipo in equipos:

        datos_equipo = df[
            df["Equipo"] == equipo
        ]

        plt.plot(
            datos_equipo["Temporada"],
            datos_equipo["Posición"],
            marker="o",
            label=equipo
        )

    plt.xlabel("Temporada")
    plt.ylabel("Posición final")

    plt.title(
        "Evolución de la posición de equipos representativos"
    )

    plt.gca().invert_yaxis()

    plt.xticks(
        rotation=45
    )

    plt.grid(
        True,
        alpha=0.25
    )

    plt.legend()

    plt.tight_layout()

    ruta_grafica = (
        carpeta_salida
        / "03_evolucion_posiciones.png"
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

    (
        df_resumen,
        df_evolucion,
        df_cambios
    ) = cargar_datos()

    graficar_estabilidad(
        df_resumen
    )

    graficar_rango(
        df_resumen
    )

    graficar_evolucion(
        df_resumen,
        df_evolucion
    )


if __name__ == "__main__":
    main()