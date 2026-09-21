from pathlib import Path
import pandas as pd
import os


def detectar_duplicados(df):

    """
    Detección de duplicados:
    Identifica registros que son exactamente iguales en todos
    los valores de sus columnas.
    """

    # Identificar registros duplicados
    duplicados = df[df.duplicated(keep=False)]

    # Cantidad de registros duplicados
    cantidad_duplicados = df.duplicated().sum()

    print("Cantidad de duplicados:", cantidad_duplicados)

    columnas = df.columns.tolist()

    # Agrupar registros exactamente iguales
    grupos = df.groupby(
        columnas,
        sort=False,
        dropna=False
    )

    grupo_numero = 0
    registros_duplicados = 0

    ruta_base = Path(__file__).resolve().parent

    ruta_txt = ruta_base / "grupos_duplicados.txt"

    """
    Se exportan los registros encontrados como duplicados,
    mostrando el primero como original y los siguientes como
    registros duplicados.
    """

    with open(ruta_txt, "w", encoding="utf-8") as archivo:

        archivo.write("========================================\n")
        archivo.write("GRUPOS DE REGISTROS DUPLICADOS\n")
        archivo.write("========================================\n")

        for _, grupo in grupos:

            if len(grupo) > 1:

                grupo_numero += 1
                registros_duplicados += len(grupo) - 1

                archivo.write(
                    f"\nGRUPO DE DUPLICADOS #{grupo_numero}\n"
                )
                archivo.write("----------------------------------------\n")

                for i, (indice, registro) in enumerate(
                    grupo.iterrows()
                ):

                    if i == 0:
                        archivo.write(
                            f"\n{indice} - registro (original)\n"
                        )
                    else:
                        archivo.write(
                            f"\n{indice} - registro (duplicado)\n"
                        )

                    archivo.write(registro.to_string())
                    archivo.write("\n")

        archivo.write(
            "\n========================================\n"
        )

        archivo.write(
            f"Total de grupos duplicados: {grupo_numero}\n"
        )

        archivo.write(
            f"Total de registros duplicados: "
            f"{registros_duplicados}\n"
        )

    print("\nReporte generado.")

    opcion = input("\n¿Deseas abrir el reporte? (s/n): ")

    if opcion.lower() == "s":
        os.startfile(ruta_txt)

    # Guardar únicamente las copias que serán eliminadas
    duplicados_eliminados = df[
        df.duplicated(keep="first")
    ]

    # Crear dataset sin duplicados
    df_limpio = df.drop_duplicates(
        keep="first"
    )

    ruta_datos = ruta_base / "Datos"

    ruta_datos.mkdir(
        parents=True,
        exist_ok=True
    )

    ruta_limpio = (
        ruta_datos
        / "dataset sin duplicados.xlsx"
    )

    ruta_duplicados = (
        ruta_datos
        / "duplicados eliminados.xlsx"
    )

    df_limpio.to_excel(
        ruta_limpio,
        index=False
    )

    duplicados_eliminados.to_excel(
        ruta_duplicados,
        index=False
    )

    print("\nArchivos generados:")
    print(f"- {ruta_limpio}")
    print(f"- {ruta_duplicados}")

    return df_limpio