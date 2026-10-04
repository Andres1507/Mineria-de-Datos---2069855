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
    / "6 - Evolucion de la clasificacion durante una temporada.xlsx"
)

carpeta_salida = (
    carpeta_script.parent
    / "doc"
    / "Graficas"
    / "06 - Evolucion de la clasificacion durante una temporada"
)

carpeta_salida.mkdir(
    parents=True,
    exist_ok=True
)


# CARGAR DATOS

def cargar_datos():

    df_resumen = pd.read_excel(
        archivo_excel,
        sheet_name="Resumen temporadas"
    )

    df_inicio_mitad_final = pd.read_excel(
        archivo_excel,
        sheet_name="Inicio mitad final"
    )

    return (
        df_resumen,
        df_inicio_mitad_final
    )


# GRAFICAR CAMBIO PROMEDIO

def graficar_cambio_promedio(df):

    plt.figure(figsize=(12, 6))

    plt.plot(
        df["Temporada"],
        df["Cambio promedio por etapa 1-19"],
        marker="o",
        label="Primera mitad"
    )

    plt.plot(
        df["Temporada"],
        df["Cambio promedio por etapa 20-38"],
        marker="o",
        label="Segunda mitad"
    )

    plt.xlabel("Temporada")
    plt.ylabel("Cambio promedio de posición")

    plt.title(
        "Cambio promedio de posición durante la temporada"
    )

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
        / "01_cambio_promedio_por_etapa.png"
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


# GRAFICAR POSICIONES QUE SE MANTIENEN

def graficar_posiciones_mantenidas(df):

    plt.figure(figsize=(12, 6))

    plt.plot(
        df["Temporada"],
        df["% de posiciones que se mantienen 1-19"],
        marker="o",
        label="Primera mitad"
    )

    plt.plot(
        df["Temporada"],
        df["% de posiciones que se mantienen 20-38"],
        marker="o",
        label="Segunda mitad"
    )

    plt.xlabel("Temporada")
    plt.ylabel("Porcentaje de posiciones que se mantienen")

    plt.title(
        "Estabilidad de las posiciones durante la temporada"
    )

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
        / "02_posiciones_mantenidas.png"
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


# GRAFICAR CAMBIOS DE LIDER

def graficar_cambios_lider(df):

    plt.figure(figsize=(12, 6))

    plt.bar(
        df["Temporada"],
        df["Cambios de líder"]
    )

    plt.xlabel("Temporada")
    plt.ylabel("Número de cambios de líder")

    plt.title(
        "Cambios de líder durante cada temporada"
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
        / "03_cambios_de_lider.png"
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
        df_inicio_mitad_final
    ) = cargar_datos()

    graficar_cambio_promedio(
        df_resumen
    )

    graficar_posiciones_mantenidas(
        df_resumen
    )

    graficar_cambios_lider(
        df_resumen
    )


if __name__ == "__main__":
    main()