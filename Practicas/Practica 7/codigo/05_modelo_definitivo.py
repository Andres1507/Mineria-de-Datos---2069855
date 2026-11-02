
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score


# RUTAS

carpeta_script = Path(__file__).resolve().parent
carpeta_practica = carpeta_script.parent

archivo_matriz = (
    carpeta_practica / "doc" / "resultados"
    / "01_matriz_perfiles_clubes.xlsx"
)

carpeta_resultados = carpeta_practica / "doc" / "resultados"
carpeta_graficas = carpeta_practica / "doc" / "Graficas"

carpeta_resultados.mkdir(parents=True, exist_ok=True)
carpeta_graficas.mkdir(parents=True, exist_ok=True)

archivo_salida = (
    carpeta_resultados / "05_modelo_definitivo.xlsx"
)


# CONFIGURACION DEL MODELO

K = 4
SEMILLA = 42
N_INIT = 20

VARIABLES = [
    "Posición promedio",
    "GF/PJ",
    "GC/PJ",
    "% Top 6",
    "% Zona baja"
]


# CARGAR DATOS

def cargar_datos():

    if not archivo_matriz.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo:\n{archivo_matriz}"
        )

    perfiles = pd.read_excel(
        archivo_matriz,
        sheet_name="Perfiles históricos"
    )

    datos = pd.read_excel(
        archivo_matriz,
        sheet_name="Modelo B"
    )

    if len(perfiles) != 34:
        raise ValueError(
            f"Se esperaban 34 clubes y se encontraron {len(perfiles)}."
        )

    if datos["Equipo"].duplicated().any():
        raise ValueError("Existen clubes duplicados.")

    if datos[VARIABLES].isnull().any().any():
        raise ValueError("Existen valores faltantes.")

    return perfiles, datos


# ENTRENAR MODELO DEFINITIVO

def entrenar_modelo(datos):

    equipos = datos["Equipo"].copy()
    variables = datos[VARIABLES].copy()

    escalador = StandardScaler()
    datos_escalados = escalador.fit_transform(variables)

    modelo = KMeans(
        n_clusters=K,
        random_state=SEMILLA,
        n_init=N_INIT
    )

    etiquetas = modelo.fit_predict(datos_escalados)

    # ASIGNAR CLUSTERS

    asignaciones = pd.DataFrame({
        "Equipo": equipos,
        "Cluster": etiquetas + 1
    })

    # CALCULAR SILHOUETTE

    silhouette = silhouette_score(
        datos_escalados,
        etiquetas
    )

    # CENTROIDES EN ESCALA ORIGINAL

    centroides_originales = escalador.inverse_transform(
        modelo.cluster_centers_
    )

    centroides = pd.DataFrame(
        centroides_originales,
        columns=VARIABLES
    )

    centroides.insert(
        0,
        "Cluster",
        range(1, K + 1)
    )

    # CENTROIDES ESTANDARIZADOS

    centroides_escalados = pd.DataFrame(
        modelo.cluster_centers_,
        columns=VARIABLES
    )

    centroides_escalados.insert(
        0,
        "Cluster",
        range(1, K + 1)
    )

    return (
        asignaciones,
        modelo,
        escalador,
        datos_escalados,
        centroides,
        centroides_escalados,
        silhouette
    )


# CARACTERIZAR LOS CLUSTERS

def caracterizar_clusters(perfiles, asignaciones):

    df = perfiles.merge(
        asignaciones,
        on="Equipo",
        how="inner",
        validate="one_to_one"
    )

    resumen = df.groupby("Cluster").agg(
        Clubes=("Equipo", "count"),
        Temporadas_promedio=("Temporadas participadas", "mean"),
        Posición_promedio=("Posición promedio", "mean"),
        GF_PJ=("GF/PJ", "mean"),
        GC_PJ=("GC/PJ", "mean"),
        Porcentaje_Top4=("% Top 4", "mean"),
        Porcentaje_Top6=("% Top 6", "mean"),
        Porcentaje_zona_baja=("% Zona baja", "mean"),
        Porcentaje_descenso=("% Zona descenso", "mean"),
        Porcentaje_posicion_17=("% Posición 17", "mean")
    ).reset_index()

    return df, resumen


# GRAFICA DE PERFILES

def graficar_perfiles(centroides):

    variables = VARIABLES

    datos = centroides[variables].copy()

    desviaciones = datos.std(ddof=0).replace(0, 1)

    datos_estandarizados = (
        datos - datos.mean()
    ) / desviaciones

    plt.figure(figsize=(10, 6))

    for indice, fila in datos_estandarizados.iterrows():

        plt.plot(
            variables,
            fila.values,
            marker="o",
            label=f"Cluster {int(centroides.iloc[indice]['Cluster'])}"
        )

    plt.axhline(
        0,
        linestyle="--",
        alpha=0.5
    )

    plt.title("Perfiles competitivos - Modelo definitivo")
    plt.ylabel("Promedio estandarizado entre clusters")
    plt.xticks(rotation=20, ha="right")
    plt.legend()
    plt.grid(alpha=0.3)

    plt.tight_layout()

    plt.savefig(
        carpeta_graficas / "05_perfiles_definitivos.png",
        dpi=300
    )

    plt.close()


# GRAFICA DE DISTRIBUCION

def graficar_distribucion(df):

    plt.figure(figsize=(12, 7))

    for cluster in sorted(df["Cluster"].unique()):

        grupo = df[df["Cluster"] == cluster]

        plt.scatter(
            grupo["Posición promedio"],
            grupo["GF/PJ"],
            label=f"Cluster {cluster}",
            s=70
        )

        for _, fila in grupo.iterrows():

            plt.annotate(
                fila["Equipo"],
                (
                    fila["Posición promedio"],
                    fila["GF/PJ"]
                ),
                fontsize=7,
                alpha=0.8
            )

    plt.title("Distribución de clubes - Modelo definitivo")
    plt.xlabel("Posición promedio (menor es mejor)")
    plt.ylabel("Goles a favor por partido")
    plt.legend()
    plt.grid(alpha=0.3)

    plt.tight_layout()

    plt.savefig(
        carpeta_graficas / "06_distribucion_definitiva.png",
        dpi=300
    )

    plt.close()


# GRAFICA DE TAMAÑO DE CLUSTERS

def graficar_tamanos(resumen):

    plt.figure(figsize=(8, 5))

    plt.bar(
        resumen["Cluster"].astype(str),
        resumen["Clubes"]
    )

    plt.title("Distribución de clubes por cluster")
    plt.xlabel("Cluster")
    plt.ylabel("Cantidad de clubes")
    plt.grid(axis="y", alpha=0.3)

    plt.tight_layout()

    plt.savefig(
        carpeta_graficas / "07_tamanos_clusters.png",
        dpi=300
    )

    plt.close()


# GUARDAR RESULTADOS

def guardar_resultados(
    df,
    resumen,
    centroides,
    centroides_escalados,
    silhouette,
    modelo
):

    indicadores = pd.DataFrame({
        "Indicador": [
            "Algoritmo",
            "Modelo seleccionado",
            "Número de clusters",
            "Número de clubes",
            "Variables utilizadas",
            "Semilla",
            "Inicializaciones",
            "Inercia final",
            "Coeficiente Silhouette"
        ],
        "Resultado": [
            "K-Means",
            "Modelo B",
            K,
            len(df),
            len(VARIABLES),
            SEMILLA,
            N_INIT,
            modelo.inertia_,
            silhouette
        ]
    })

    with pd.ExcelWriter(archivo_salida) as writer:

        df.to_excel(
            writer,
            sheet_name="Clubes clasificados",
            index=False
        )

        resumen.to_excel(
            writer,
            sheet_name="Resumen de clusters",
            index=False
        )

        centroides.to_excel(
            writer,
            sheet_name="Centroides originales",
            index=False
        )

        centroides_escalados.to_excel(
            writer,
            sheet_name="Centroides escalados",
            index=False
        )

        indicadores.to_excel(
            writer,
            sheet_name="Indicadores del modelo",
            index=False
        )


# EJECUCION PRINCIPAL

def main():

    print("\nMODELO DEFINITIVO K-MEANS - PRACTICA 7\n")

    perfiles, datos = cargar_datos()

    (
        asignaciones,
        modelo,
        escalador,
        datos_escalados,
        centroides,
        centroides_escalados,
        silhouette
    ) = entrenar_modelo(datos)

    df, resumen = caracterizar_clusters(
        perfiles,
        asignaciones
    )

    graficar_perfiles(centroides)
    graficar_distribucion(df)
    graficar_tamanos(resumen)

    guardar_resultados(
        df,
        resumen,
        centroides,
        centroides_escalados,
        silhouette,
        modelo
    )

    print(f"Clubes clasificados: {len(df)}")
    print(f"Clusters generados: {K}")
    print(f"Inercia final: {modelo.inertia_:.4f}")
    print(f"Silhouette final: {silhouette:.4f}")

    print("\nDISTRIBUCION DE CLUSTERS")
    print(resumen.to_string(index=False))

    print("\nCLUBES POR CLUSTER")

    for cluster, grupo in df.groupby("Cluster"):

        print(
            f"\nCluster {cluster}: "
            + ", ".join(grupo["Equipo"].tolist())
        )

    print("\nARCHIVO GENERADO:")
    print(archivo_salida)

    print("\nGRAFICAS GUARDADAS EN:")
    print(carpeta_graficas)


if __name__ == "__main__":
    main()
