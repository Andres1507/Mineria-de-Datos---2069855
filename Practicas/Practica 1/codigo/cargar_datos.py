from pathlib import Path
import pandas as pd


def cargar_datos():

    # Encontrar la ruta del archivo original
    dataset = (
        Path(__file__).resolve().parents[2]
        / "Dataset"
        / "Dataset original"
        / "resultados_futbol_liga_espanola.xlsx"
    )

    # Leer el conjunto de datos
    df = pd.read_excel(dataset)

    return df