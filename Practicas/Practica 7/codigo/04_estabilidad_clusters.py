
from pathlib import Path

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import adjusted_rand_score, silhouette_score


# RUTAS

carpeta_script = Path(__file__).resolve().parent
carpeta_practica = carpeta_script.parent

archivo_excel = (
    carpeta_practica / "doc" / "resultados"
    / "01_matriz_perfiles_clubes.xlsx"
)

carpeta_resultados = carpeta_practica / "doc" / "resultados"
carpeta_resultados.mkdir(parents=True, exist_ok=True)

archivo_salida = carpeta_resultados / "04_estabilidad_clusters.xlsx"


# CONFIGURACION

K_CANDIDATOS = [3, 4]
SEMILLA_REFERENCIA = 42
REPETICIONES = 50
N_INIT = 20


# CARGAR DATOS

def cargar_datos():

    if not archivo_excel.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo:\n{archivo_excel}"
        )

    df = pd.read_excel(
        archivo_excel,
        sheet_name="Modelo B"
    )

    equipos = df["Equipo"].copy()
    variables = df.drop(columns=["Equipo"])

    if variables.isnull().any().any():
        raise ValueError("Hay valores faltantes en las variables.")

    escalador = StandardScaler()
    datos = escalador.fit_transform(variables)

    return equipos, datos


# EVALUAR ESTABILIDAD

def evaluar_estabilidad(equipos, datos, k):

    modelo_referencia = KMeans(
        n_clusters=k,
        random_state=SEMILLA_REFERENCIA,
        n_init=N_INIT
    )

    etiquetas_referencia = modelo_referencia.fit_predict(datos)

    resultados = []

    for semilla in range(REPETICIONES):

        modelo = KMeans(
            n_clusters=k,
            random_state=semilla,
            n_init=N_INIT
        )

        etiquetas = modelo.fit_predict(datos)

        ari = adjusted_rand_score(
            etiquetas_referencia,
            etiquetas
        )

        silhouette = silhouette_score(
            datos,
            etiquetas
        )

        resultados.append({
            "K": k,
            "Semilla": semilla,
            "ARI": ari,
            "Silhouette": silhouette,
            "Inercia": modelo.inertia_
        })

    resultados = pd.DataFrame(resultados)

    resumen = pd.DataFrame([{
        "K": k,
        "ARI promedio": resultados["ARI"].mean(),
        "ARI mínimo": resultados["ARI"].min(),
        "ARI máximo": resultados["ARI"].max(),
        "Silhouette promedio": resultados["Silhouette"].mean(),
        "Silhouette mínimo": resultados["Silhouette"].min(),
        "Silhouette máximo": resultados["Silhouette"].max(),
        "Inercia promedio": resultados["Inercia"].mean()
    }])

    return resultados, resumen


# GUARDAR RESULTADOS

def guardar_resultados(detalles, resumen):

    with pd.ExcelWriter(archivo_salida) as writer:

        pd.concat(
            detalles,
            ignore_index=True
        ).to_excel(
            writer,
            sheet_name="Ejecuciones",
            index=False
        )

        pd.concat(
            resumen,
            ignore_index=True
        ).to_excel(
            writer,
            sheet_name="Resumen",
            index=False
        )


# EJECUCION PRINCIPAL

def main():

    print("\nESTABILIDAD DE CLUSTERS - PRACTICA 7\n")

    equipos, datos = cargar_datos()

    print(f"Clubes analizados: {len(equipos)}")
    print(f"Repeticiones por modelo: {REPETICIONES}")

    detalles = []
    resumenes = []

    for k in K_CANDIDATOS:

        print(f"\nEvaluando K={k}...")

        resultados, resumen = evaluar_estabilidad(
            equipos,
            datos,
            k
        )

        detalles.append(resultados)
        resumenes.append(resumen)

        print(resumen.to_string(index=False))

    guardar_resultados(
        detalles,
        resumenes
    )

    print("\nRESULTADOS GUARDADOS EN:")
    print(archivo_salida)


if __name__ == "__main__":
    main()
