from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler

# RUTAS
carpeta_script = Path(__file__).resolve().parent
carpeta_practica = carpeta_script.parent
archivo_excel = (
    carpeta_script.parents[1] / "Practica 2" / "doc" / "resultados"
    / "5 - Estabilidad y evolucion individual de los equipos.xlsx"
)
carpeta_resultados = carpeta_practica / "doc" / "resultados"
carpeta_graficas = carpeta_practica / "doc" / "Graficas"
carpeta_resultados.mkdir(parents=True, exist_ok=True)
carpeta_graficas.mkdir(parents=True, exist_ok=True)

# CONFIGURACION
PARTIDOS_TEMPORADA = 38
ZONAS = ["1.º-5.º", "6.º-10.º", "11.º-15.º", "16.º-20.º"]
TEMPORADAS_ENTRENAMIENTO = 10
TEMPORADAS_VALIDACION = 2
K_CANDIDATOS = range(1, 26, 2)
VARIABLES_BASE = ["GF/PJ", "GC/PJ"]
VARIABLES_ALTERNATIVAS = ["GF/PJ", "GC/PJ", "DG/PJ"]


# CARGAR Y PREPARAR DATOS
def cargar_datos():
    if not archivo_excel.exists():
        raise FileNotFoundError(
            "No se encontró el archivo de resultados de la Práctica 2:\n"
            f"{archivo_excel}\nSe recomienda usar la estructura original de carpetas."
        )

    df = pd.read_excel(archivo_excel, sheet_name="Evolución por temporada")
    columnas = ["Temporada", "Equipo", "Posición", "Puntos", "Goles a favor", "Goles en contra"]
    df = df[columnas].copy()

    if df[columnas].isnull().any().any():
        raise ValueError("Hay valores faltantes en las columnas necesarias.")
    if df.duplicated(["Temporada", "Equipo"]).any():
        raise ValueError("Hay registros duplicados por temporada y equipo.")
    if not df["Posición"].between(1, 20).all():
        raise ValueError("Hay posiciones fuera del rango esperado de 1 a 20.")

    df["GF/PJ"] = df["Goles a favor"] / PARTIDOS_TEMPORADA
    df["GC/PJ"] = df["Goles en contra"] / PARTIDOS_TEMPORADA
    df["DG/PJ"] = (df["Goles a favor"] - df["Goles en contra"]) / PARTIDOS_TEMPORADA
    df["Zona"] = pd.cut(
        df["Posición"], bins=[0, 5, 10, 15, 20], labels=ZONAS, include_lowest=True
    ).astype(str)

    orden_temporadas = sorted(df["Temporada"].unique(), key=lambda x: str(x))
    if len(orden_temporadas) < TEMPORADAS_ENTRENAMIENTO + TEMPORADAS_VALIDACION + 1:
        raise ValueError("No hay suficientes temporadas para la separación temporal definida.")
    if len(df) != 300:
        print(f"Aviso: se esperaban 300 registros y se encontraron {len(df)}.")

    return df, orden_temporadas


def separar_temporadas(df, temporadas):
    n_train = TEMPORADAS_ENTRENAMIENTO
    n_val = n_train + TEMPORADAS_VALIDACION
    temporadas_train = temporadas[:n_train]
    temporadas_val = temporadas[n_train:n_val]
    temporadas_test = temporadas[n_val:]
    train = df[df["Temporada"].isin(temporadas_train)].copy()
    validacion = df[df["Temporada"].isin(temporadas_val)].copy()
    prueba = df[df["Temporada"].isin(temporadas_test)].copy()
    return train, validacion, prueba, temporadas_train, temporadas_val, temporadas_test


def evaluar_k(train, validacion, variables):
    # EL ESCALADOR SE AJUSTA SOLO CON ENTRENAMIENTO
    escalador = StandardScaler()
    x_train = escalador.fit_transform(train[variables])
    x_val = escalador.transform(validacion[variables])
    y_train = train["Zona"]
    y_val = validacion["Zona"]
    filas = []

    for k in K_CANDIDATOS:
        if k > len(train):
            continue
        modelo = KNeighborsClassifier(n_neighbors=k, weights="uniform", metric="minkowski", p=2)
        modelo.fit(x_train, y_train)
        pred = modelo.predict(x_val)
        filas.append({
            "Variables": " + ".join(variables), "K": k,
            "Exactitud validación": accuracy_score(y_val, pred),
            "F1 macro validación": f1_score(y_val, pred, labels=ZONAS, average="macro", zero_division=0)
        })

    tabla = pd.DataFrame(filas)
    mejor = tabla.sort_values(
        ["F1 macro validación", "Exactitud validación", "K"],
        ascending=[False, False, True]
    ).iloc[0]
    return int(mejor["K"]), tabla


def entrenar_y_evaluar(train, prueba, variables, k, nombre_modelo):
    # REAJUSTAR EL ESCALADOR Y EL MODELO CON ENTRENAMIENTO + VALIDACION
    escalador = StandardScaler()
    x_train = escalador.fit_transform(train[variables])
    x_test = escalador.transform(prueba[variables])
    y_train = train["Zona"]
    y_test = prueba["Zona"]

    modelo = KNeighborsClassifier(n_neighbors=k, weights="uniform", metric="minkowski", p=2)
    modelo.fit(x_train, y_train)
    pred = modelo.predict(x_test)

    metricas = {
        "Modelo": nombre_modelo,
        "Variables": " + ".join(variables),
        "K seleccionado": k,
        "Registros entrenamiento": len(train),
        "Registros prueba": len(prueba),
        "Exactitud": accuracy_score(y_test, pred),
        "Precisión macro": precision_score(y_test, pred, labels=ZONAS, average="macro", zero_division=0),
        "Recall macro": recall_score(y_test, pred, labels=ZONAS, average="macro", zero_division=0),
        "F1 macro": f1_score(y_test, pred, labels=ZONAS, average="macro", zero_division=0)
    }
    matriz = pd.DataFrame(
        confusion_matrix(y_test, pred, labels=ZONAS),
        index=[f"Real {z}" for z in ZONAS],
        columns=[f"Predicho {z}" for z in ZONAS]
    )
    reporte = pd.DataFrame(classification_report(
        y_test, pred, labels=ZONAS, output_dict=True, zero_division=0
    )).T.reset_index(names="Clase")
    predicciones = prueba[["Temporada", "Equipo", "Posición", "Zona", "GF/PJ", "GC/PJ", "DG/PJ"]].copy()
    predicciones["Zona predicha"] = pred
    predicciones["Correcto"] = predicciones["Zona"] == predicciones["Zona predicha"]
    predicciones["Modelo"] = nombre_modelo
    return metricas, matriz, reporte, predicciones


# GRAFICAS
def guardar_distribucion(df):
    conteo = df["Zona"].value_counts().reindex(ZONAS)
    plt.figure(figsize=(8, 5))
    barras = plt.bar(conteo.index, conteo.values)
    plt.bar_label(barras)
    plt.title("Distribución de registros por zona de clasificación")
    plt.xlabel("Zona final")
    plt.ylabel("Cantidad de registros")
    plt.tight_layout()
    plt.savefig(carpeta_graficas / "01_distribucion_clases.png", dpi=300, bbox_inches="tight")
    plt.close()


def guardar_seleccion_k(tabla_k):
    plt.figure(figsize=(9, 5))
    for variables, datos in tabla_k.groupby("Variables"):
        plt.plot(datos["K"], datos["F1 macro validación"], marker="o", label=variables)
    plt.title("Selección de K mediante F1 macro en validación temporal")
    plt.xlabel("Número de vecinos (K)")
    plt.ylabel("F1 macro de validación")
    plt.xticks(sorted(tabla_k["K"].unique()))
    plt.legend()
    plt.grid(True, alpha=0.25)
    plt.tight_layout()
    plt.savefig(carpeta_graficas / "02_seleccion_k.png", dpi=300, bbox_inches="tight")
    plt.close()


def guardar_matriz_confusion(matriz, nombre_archivo="03_matriz_confusion.png"):
    valores = matriz.to_numpy()
    fig, ax = plt.subplots(figsize=(8, 6))
    imagen = ax.imshow(valores, interpolation="nearest")
    fig.colorbar(imagen, ax=ax, label="Cantidad de equipos")
    ax.set_xticks(range(len(ZONAS),), labels=ZONAS)
    ax.set_yticks(range(len(ZONAS)), labels=ZONAS)
    ax.set_xlabel("Zona predicha")
    ax.set_ylabel("Zona real")
    ax.set_title("Matriz de confusión en temporadas de prueba")
    for i in range(valores.shape[0]):
        for j in range(valores.shape[1]):
            ax.text(j, i, str(valores[i, j]), ha="center", va="center")
    plt.tight_layout()
    plt.savefig(carpeta_graficas / nombre_archivo, dpi=300, bbox_inches="tight")
    plt.close()


def guardar_comparacion(metricas):
    etiquetas = metricas["Modelo"]
    x = np.arange(len(etiquetas))
    ancho = 0.25
    plt.figure(figsize=(10, 6))
    for i, columna in enumerate(["Exactitud", "Precisión macro", "Recall macro", "F1 macro"]):
        plt.bar(x + (i - 1.5) * ancho, metricas[columna], ancho, label=columna)
    plt.xticks(x, etiquetas, rotation=10, ha="right")
    plt.ylim(0, 1)
    plt.ylabel("Valor de la métrica")
    plt.title("Comparación de modelos KNN en temporadas no vistas")
    plt.legend()
    plt.tight_layout()
    plt.savefig(carpeta_graficas / "04_comparacion_modelos.png", dpi=300, bbox_inches="tight")
    plt.close()


def main():
    df, temporadas = cargar_datos()
    train, validacion, prueba, temporadas_train, temporadas_val, temporadas_test = separar_temporadas(df, temporadas)

    # SELECCIONAR K SIN USAR LAS TEMPORADAS DE PRUEBA
    k_base, tabla_k_base = evaluar_k(train, validacion, VARIABLES_BASE)
    k_alt, tabla_k_alt = evaluar_k(train, validacion, VARIABLES_ALTERNATIVAS)
    tabla_k = pd.concat([tabla_k_base, tabla_k_alt], ignore_index=True)

    # REENTRENAR CON LAS TEMPORADAS DE ENTRENAMIENTO Y VALIDACION
    train_final = pd.concat([train, validacion], ignore_index=True)
    metricas_base, matriz_base, reporte_base, pred_base = entrenar_y_evaluar(
        train_final, prueba, VARIABLES_BASE, k_base, "KNN base (GF/PJ, GC/PJ)"
    )
    metricas_alt, matriz_alt, reporte_alt, pred_alt = entrenar_y_evaluar(
        train_final, prueba, VARIABLES_ALTERNATIVAS, k_alt, "KNN con diferencia de goles"
    )

    tabla_metricas = pd.DataFrame([metricas_base, metricas_alt])
    tabla_predicciones = pd.concat([pred_base, pred_alt], ignore_index=True)
    tabla_reportes = pd.concat([
        reporte_base.assign(Modelo=metricas_base["Modelo"]),
        reporte_alt.assign(Modelo=metricas_alt["Modelo"])
    ], ignore_index=True)
    tabla_temporadas = pd.DataFrame([
        {"Conjunto": "Entrenamiento inicial", "Temporadas": ", ".join(map(str, temporadas_train)), "Registros": len(train)},
        {"Conjunto": "Validación", "Temporadas": ", ".join(map(str, temporadas_val)), "Registros": len(validacion)},
        {"Conjunto": "Prueba final", "Temporadas": ", ".join(map(str, temporadas_test)), "Registros": len(prueba)}
    ])

    guardar_distribucion(df)
    guardar_seleccion_k(tabla_k)
    guardar_matriz_confusion(matriz_base)
    guardar_comparacion(tabla_metricas)

    with pd.ExcelWriter(carpeta_resultados / "resultados_practica6.xlsx") as escritor:
        tabla_metricas.to_excel(escritor, sheet_name="Comparación de modelos", index=False)
        tabla_k.to_excel(escritor, sheet_name="Selección de K", index=False)
        tabla_temporadas.to_excel(escritor, sheet_name="Separación temporal", index=False)
        matriz_base.to_excel(escritor, sheet_name="Matriz KNN base")
        matriz_alt.to_excel(escritor, sheet_name="Matriz KNN alternativa")
        tabla_reportes.to_excel(escritor, sheet_name="Métricas por zona", index=False)
        tabla_predicciones.to_excel(escritor, sheet_name="Predicciones de prueba", index=False)
        df.to_excel(escritor, sheet_name="Datos preparados", index=False)

    print("\nPRACTICA 6 - CLASIFICACION KNN")
    print("Temporadas de entrenamiento:", ", ".join(map(str, temporadas_train)))
    print("Temporadas de validación:", ", ".join(map(str, temporadas_val)))
    print("Temporadas de prueba:", ", ".join(map(str, temporadas_test)))
    print("\nMÉTRICAS EN TEMPORADAS DE PRUEBA")
    print(tabla_metricas.to_string(index=False))
    print(f"\nResultados: {carpeta_resultados / 'resultados_practica6.xlsx'}")
    print(f"Gráficas: {carpeta_graficas}")


if __name__ == "__main__":
    main()
