
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


# RUTAS

carpeta_script = Path(__file__).resolve().parent
carpeta_practica = carpeta_script.parent

archivo_perfiles = (
    carpeta_practica / "doc" / "resultados"
    / "01_matriz_perfiles_clubes.xlsx"
)

archivo_modelos = (
    carpeta_practica / "doc" / "resultados"
    / "02_evaluacion_kmeans.xlsx"
)

carpeta_resultados = carpeta_practica / "doc" / "resultados"
carpeta_graficas = carpeta_practica / "doc" / "Graficas"

carpeta_resultados.mkdir(parents=True, exist_ok=True)
carpeta_graficas.mkdir(parents=True, exist_ok=True)

archivo_salida = carpeta_resultados / "03_caracterizacion_clusters.xlsx"


# CONFIGURACION

CANDIDATOS = [
    ("Modelo A", 2),
    ("Modelo B", 3),
    ("Modelo B", 4)
]

VARIABLES = [
    "Posición promedio",
    "GF/PJ",
    "GC/PJ",
    "% Top 6",
    "% Zona baja"
]


# CARGAR DATOS

def cargar_datos():

    if not archivo_perfiles.exists() or not archivo_modelos.exists():
        raise FileNotFoundError(
            "No se encontraron los archivos de las etapas anteriores."
        )

    perfiles = pd.read_excel(
        archivo_perfiles,
        sheet_name="Perfiles históricos"
    )

    asignaciones = pd.read_excel(
        archivo_modelos,
        sheet_name="Asignaciones"
    )

    return perfiles, asignaciones


# CARACTERIZAR CLUSTERS

def caracterizar_modelo(perfiles, asignaciones, nombre, k):

    asignacion = asignaciones[
        (asignaciones["Modelo"] == nombre) &
        (asignaciones["K"] == k)
    ][["Equipo", "Cluster"]].copy()

    if len(asignacion) != len(perfiles):
        raise ValueError(
            f"Las asignaciones de {nombre}, K={k}, "
            "no contienen todos los clubes."
        )

    df = perfiles.merge(
        asignacion,
        on="Equipo",
        how="inner",
        validate="one_to_one"
    )

    variables_disponibles = [
        col for col in VARIABLES if col in df.columns
    ]

    resumen = df.groupby("Cluster").agg(
        Clubes=("Equipo", "count"),
        Temporadas_promedio=("Temporadas participadas", "mean"),
        **{
            variable: (variable, "mean")
            for variable in variables_disponibles
        }
    ).reset_index()

    resumen.insert(0, "Modelo", nombre)
    resumen.insert(1, "K", k)

    miembros = df[
        ["Equipo", "Cluster", "Temporadas participadas"]
        + variables_disponibles
    ].sort_values(["Cluster", "Equipo"])

    miembros.insert(0, "Modelo", nombre)
    miembros.insert(1, "K", k)

    return df, resumen, miembros


# GRAFICA DE PERFILES

def graficar_perfiles(resumen, nombre, k):

    variables = [
        col for col in VARIABLES if col in resumen.columns
    ]

    datos = resumen[variables].copy()

    # ESTANDARIZAR PROMEDIOS PARA COMPARAR DIMENSIONES

    desviaciones = datos.std(ddof=0).replace(0, 1)
    datos = (datos - datos.mean()) / desviaciones

    plt.figure(figsize=(10, 6))

    for indice, fila in datos.iterrows():

        plt.plot(
            variables,
            fila.values,
            marker="o",
            label=f"Cluster {int(resumen.iloc[indice]['Cluster'])}"
        )

    plt.axhline(0, linestyle="--", alpha=0.5)

    plt.title(f"Perfiles competitivos - {nombre}, K={k}")
    plt.ylabel("Promedio estandarizado entre clusters")
    plt.xticks(rotation=20, ha="right")
    plt.legend()
    plt.grid(alpha=0.3)

    plt.tight_layout()

    archivo = (
        f"01_perfiles_{nombre[-1].lower()}_k{k}.png"
    )

    plt.savefig(
        carpeta_graficas / archivo,
        dpi=300
    )

    plt.close()


# GRAFICA DE DISTRIBUCION

def graficar_posiciones(df, nombre, k):

    plt.figure(figsize=(10, 6))

    for cluster in sorted(df["Cluster"].unique()):

        grupo = df[df["Cluster"] == cluster]

        plt.scatter(
            grupo["Posición promedio"],
            grupo["GF/PJ"],
            label=f"Cluster {cluster}",
            s=65
        )

        for _, fila in grupo.iterrows():

            plt.annotate(
                fila["Equipo"],
                (fila["Posición promedio"], fila["GF/PJ"]),
                fontsize=7,
                alpha=0.8
            )

    plt.title(f"Posición y rendimiento ofensivo - {nombre}, K={k}")
    plt.xlabel("Posición promedio (menor es mejor)")
    plt.ylabel("Goles a favor por partido")
    plt.legend()
    plt.grid(alpha=0.3)

    plt.tight_layout()

    archivo = (
        f"02_distribucion_{nombre[-1].lower()}_k{k}.png"
    )

    plt.savefig(
        carpeta_graficas / archivo,
        dpi=300
    )

    plt.close()


# GUARDAR RESULTADOS

def guardar_resultados(resumenes, miembros):

    with pd.ExcelWriter(archivo_salida) as writer:

        pd.concat(
            resumenes,
            ignore_index=True
        ).to_excel(
            writer,
            sheet_name="Resumen de clusters",
            index=False
        )

        pd.concat(
            miembros,
            ignore_index=True
        ).to_excel(
            writer,
            sheet_name="Clubes por cluster",
            index=False
        )


# EJECUCION PRINCIPAL

def main():

    print("\nCARACTERIZACION DE CLUSTERS - PRACTICA 7\n")

    perfiles, asignaciones = cargar_datos()

    resumenes = []
    miembros = []

    for nombre, k in CANDIDATOS:

        print(f"\n{nombre} - K={k}")

        df, resumen, clubes = caracterizar_modelo(
            perfiles,
            asignaciones,
            nombre,
            k
        )

        resumenes.append(resumen)
        miembros.append(clubes)

        graficar_perfiles(
            resumen,
            nombre,
            k
        )

        graficar_posiciones(
            df,
            nombre,
            k
        )

        print("\nDISTRIBUCION DE CLUBES")
        print(
            resumen[
                ["Cluster", "Clubes", "Temporadas_promedio"]
            ].to_string(index=False)
        )

        print("\nPROMEDIOS POR CLUSTER")
        print(resumen.to_string(index=False))

        print("\nCLUBES")
        for cluster, grupo in clubes.groupby("Cluster"):
            print(
                f"Cluster {cluster}: "
                + ", ".join(grupo["Equipo"].tolist())
            )

    guardar_resultados(
        resumenes,
        miembros
    )

    print("\nRESULTADOS GUARDADOS EN:")
    print(archivo_salida)

    print("\nGRAFICAS GUARDADAS EN:")
    print(carpeta_graficas)


if __name__ == "__main__":
    main()
