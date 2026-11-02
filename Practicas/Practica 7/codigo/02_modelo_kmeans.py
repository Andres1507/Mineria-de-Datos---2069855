
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score


# RUTAS

carpeta_script = Path(__file__).resolve().parent
carpeta_practica = carpeta_script.parent

archivo_excel = (
    carpeta_practica / "doc" / "resultados"
    / "01_matriz_perfiles_clubes.xlsx"
)

carpeta_resultados = carpeta_practica / "doc" / "resultados"
carpeta_graficas = carpeta_practica / "doc" / "Graficas"

carpeta_resultados.mkdir(parents=True, exist_ok=True)
carpeta_graficas.mkdir(parents=True, exist_ok=True)

archivo_salida = carpeta_resultados / "02_evaluacion_kmeans.xlsx"


# CONFIGURACION

K_CANDIDATOS = range(2, 11)
SEMILLA = 42
N_INIT = 20

MODELOS = {
    "Modelo A": "Modelo A",
    "Modelo B": "Modelo B"
}


# CARGAR DATOS

def cargar_datos():

    if not archivo_excel.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo:\n{archivo_excel}"
        )

    modelos = {}

    for nombre, hoja in MODELOS.items():

        df = pd.read_excel(
            archivo_excel,
            sheet_name=hoja
        )

        if "Equipo" not in df.columns:
            raise ValueError(
                f"La hoja {hoja} no contiene la columna Equipo."
            )

        if df["Equipo"].duplicated().any():
            raise ValueError(
                f"Hay equipos duplicados en {hoja}."
            )

        if df.isnull().any().any():
            raise ValueError(
                f"Hay valores faltantes en {hoja}."
            )

        modelos[nombre] = df

    return modelos


# ESTANDARIZAR VARIABLES

def estandarizar_datos(df):

    equipos = df["Equipo"].copy()
    variables = df.drop(columns=["Equipo"])

    escalador = StandardScaler()
    datos_escalados = escalador.fit_transform(variables)

    return equipos, variables.columns.tolist(), datos_escalados


# EVALUAR K-MEANS

def evaluar_modelo(nombre, df):

    equipos, variables, datos = estandarizar_datos(df)

    resultados = []
    asignaciones = []

    for k in K_CANDIDATOS:

        modelo = KMeans(
            n_clusters=k,
            random_state=SEMILLA,
            n_init=N_INIT
        )

        etiquetas = modelo.fit_predict(datos)

        silhouette = silhouette_score(
            datos,
            etiquetas
        )

        resultados.append({
            "Modelo": nombre,
            "K": k,
            "Inercia": modelo.inertia_,
            "Silhouette": silhouette
        })

        for equipo, cluster in zip(equipos, etiquetas):

            asignaciones.append({
                "Modelo": nombre,
                "K": k,
                "Equipo": equipo,
                "Cluster": cluster + 1
            })

    return pd.DataFrame(resultados), pd.DataFrame(asignaciones)


# GENERAR GRAFICAS

def graficar_evaluacion(resultados, nombre):

    # METODO DEL CODO

    plt.figure(figsize=(9, 5))

    plt.plot(
        resultados["K"],
        resultados["Inercia"],
        marker="o"
    )

    plt.title(f"Metodo del codo - {nombre}")
    plt.xlabel("Numero de clusters (K)")
    plt.ylabel("Inercia")
    plt.xticks(list(K_CANDIDATOS))
    plt.grid(alpha=0.3)

    plt.tight_layout()

    plt.savefig(
        carpeta_graficas / f"01_codo_{nombre[-1].lower()}.png",
        dpi=300
    )

    plt.close()

    # COEFICIENTE SILHOUETTE

    plt.figure(figsize=(9, 5))

    plt.plot(
        resultados["K"],
        resultados["Silhouette"],
        marker="o"
    )

    plt.title(f"Coeficiente Silhouette - {nombre}")
    plt.xlabel("Numero de clusters (K)")
    plt.ylabel("Coeficiente Silhouette")
    plt.xticks(list(K_CANDIDATOS))
    plt.grid(alpha=0.3)

    plt.tight_layout()

    plt.savefig(
        carpeta_graficas / f"02_silhouette_{nombre[-1].lower()}.png",
        dpi=300
    )

    plt.close()


# COMPARAR MODELOS

def comparar_modelos(resultados):

    comparacion = resultados.pivot(
        index="K",
        columns="Modelo",
        values="Silhouette"
    ).reset_index()

    return comparacion


# GUARDAR RESULTADOS

def guardar_resultados(
    resultados,
    asignaciones,
    comparacion
):

    with pd.ExcelWriter(archivo_salida) as writer:

        resultados.to_excel(
            writer,
            sheet_name="Evaluación",
            index=False
        )

        comparacion.to_excel(
            writer,
            sheet_name="Comparación",
            index=False
        )

        asignaciones.to_excel(
            writer,
            sheet_name="Asignaciones",
            index=False
        )


# EJECUCION PRINCIPAL

def main():

    print("\nEVALUACION K-MEANS - PRACTICA 7\n")

    modelos = cargar_datos()

    resultados_totales = []
    asignaciones_totales = []

    for nombre, df in modelos.items():

        print(f"\nEvaluando {nombre}...")

        resultados, asignaciones = evaluar_modelo(
            nombre,
            df
        )

        resultados_totales.append(resultados)
        asignaciones_totales.append(asignaciones)

        graficar_evaluacion(
            resultados,
            nombre
        )

        mejor = resultados.loc[
            resultados["Silhouette"].idxmax()
        ]

        print(
            f"Mejor Silhouette provisional: "
            f"K={int(mejor['K'])}, "
            f"valor={mejor['Silhouette']:.4f}"
        )

    resultados = pd.concat(
        resultados_totales,
        ignore_index=True
    )

    asignaciones = pd.concat(
        asignaciones_totales,
        ignore_index=True
    )

    comparacion = comparar_modelos(resultados)

    guardar_resultados(
        resultados,
        asignaciones,
        comparacion
    )

    print("\nRESULTADOS DE EVALUACION")
    print(resultados.to_string(index=False))

    print("\nCOMPARACION DE MODELOS")
    print(comparacion.to_string(index=False))

    print("\nARCHIVO GENERADO:")
    print(archivo_salida)

    print("\nGRAFICAS GUARDADAS EN:")
    print(carpeta_graficas)


if __name__ == "__main__":
    main()
