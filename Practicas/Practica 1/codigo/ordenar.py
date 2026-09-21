
from pathlib import Path
import pandas as pd

def ordenar_por_fecha_hora(df):

    """
    Ordena el dataset cronológicamente por fecha y hora
    y guarda el resultado en un archivo Excel independiente.
    """


    df_ordenado = df.copy()

    # Combinar fecha y hora
    fecha_hora = pd.to_datetime(
        df_ordenado["Date"].dt.strftime("%Y-%m-%d")
        + " "
        + df_ordenado["Time"].astype(str),
        format="%Y-%m-%d %H:%M",
        errors="coerce"
    )

    # Ordenar
    df_ordenado = (
        df_ordenado
        .assign(FechaHora=fecha_hora)
        .sort_values("FechaHora")
        .drop(columns="FechaHora")
        .reset_index(drop=True)
    )

    carpeta_datos = (
        Path(__file__).resolve().parent / "Datos"
    )

    carpeta_datos.mkdir(
        exist_ok=True
    )

    ruta_salida = (
        carpeta_datos /
        "dataset ordenado.xlsx"
    )

    df_ordenado.to_excel(
        ruta_salida,
        index=False
    )

    print(
        "\n -- El Dataset se encuentra ordenado por fecha y hora --"
    )

    print(
        "\nArchivo generado:"
    )

    print(
        ruta_salida
    )

    return df_ordenado