
from pathlib import Path
import pandas as pd
import os

def detectar_duplicados(df):

    """
    Deteccion de duplicados: observar si en el conjunto existen registros duplicados
    (exactamente iguales en todos los valores de sus columnas)
    """

    # Identificar registros duplicados
    duplicados = df[df.duplicated(keep=False)]

    # Cantidad de registros duplicados
    cantidad_duplicados = df.duplicated().sum()

    print("Cantidad de duplicados:", cantidad_duplicados)

    columnas = df.columns.tolist()

    grupos = df.groupby(
        columnas,
        sort=False,
        dropna=False
    )

    grupo_numero = 0
    registros_duplicados = 0

    ruta_txt = Path(__file__).resolve().parent / "grupos_duplicados.txt"

    """Aqui se exportan los registros que se encontraon duplicados por 'pares', mostrando el primero como original y el que encontro igual como su replica
        asi podemos observar si realmente son exactamente iguales, al final nos dice la cantida de registros que se encontraron con una copia."""
    
    with open(ruta_txt, "w", encoding="utf-8") as archivo:

        archivo.write("========================================\n")
        archivo.write("GRUPOS DE REGISTROS DUPLICADOS\n")
        archivo.write("========================================\n")

        for _, grupo in grupos:

            if len(grupo) > 1:

                grupo_numero += 1
                registros_duplicados += len(grupo) - 1

                for i, (indice, registro) in enumerate(grupo.iterrows()):

                    if i == 0:
                        archivo.write(
                            f"\n {indice} - registro (original)\n"
                        )
                    else:
                        archivo.write(
                            f"\n {indice} - registro\n"
                        )

                    archivo.write(registro.to_string())
                    archivo.write("\n")

        archivo.write(
            f"\nTotal de registros duplicados: {registros_duplicados}\n"
        )

    print("\nReporte generado")

    opcion = input("\n¿Deseas abrir el reporte? (s/n): ")

    if opcion.lower() == "s":
        
        os.startfile(ruta_txt)

    # Exportar dataset limpio y duplicados eliminados

    duplicados_eliminados = df[df.duplicated(keep="first")]

    df_limpio = df.drop_duplicates(keep="first")

    ruta_limpio = (
        Path(__file__).resolve().parent
        / "Datos"
        / "dataset sin duplicados.xlsx"
    )

    ruta_duplicados = (
        Path(__file__).resolve().parent
        / "Datos"
        / "duplicados eliminados.xlsx"
    )

    df_limpio.to_excel(ruta_limpio, index=False)
    duplicados_eliminados.to_excel(ruta_duplicados, index=False)

    print("\nArchivos generados.")

    return df_limpio