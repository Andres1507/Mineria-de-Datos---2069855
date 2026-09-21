
import pandas as pd
from pathlib import Path
from datetime import datetime

def verificar_dataset(df):
    
    """
    Aqui verificamos que el dataset este limpio en base a los criterios y procesos que 
    definimos como las fases de limpieza en los otros scripts

    Revisa:
    - Dimensiones
    - Valores faltantes
    - Duplicados
    - Tipos de datos
    - Fechas
    - Valores negativos en goles
    - Categorías de FTR
    - Nombres de equipos

    Si todas las verificaciones son correctas,
    exporta el dataset final a la carpeta Datos.
    """

    todo_correcto = True

    # 1. Dimensiones
    filas, columnas = df.shape

    print("\n1. DIMENSIONES")
    print(f"Filas: {filas}")
    print(f"Columnas: {columnas}")

    # 2. Valores faltantes
    print("\n2. VALORES FALTANTES")

    faltantes = df.isnull().sum()
    total_faltantes = faltantes.sum()

    if total_faltantes == 0:

        print(" -- No existen valores faltantes --")

    else:

        print(" -- Existen valores faltantes --")

        print(
            faltantes[
                faltantes > 0
            ]
        )

        todo_correcto = False

    # 3. Duplicados
    print("\n3. DUPLICADOS")

    duplicados = df.duplicated().sum()

    if duplicados == 0:

        print(" -- No existen registros duplicados --")

    else:

        print(
            f" -- Existen {duplicados} registros duplicados --"
        )

        todo_correcto = False

    # 4. Tipos de datos
    print("\n4. TIPOS DE DATOS")

    print(df.dtypes)

    # Verificar Date
    if not pd.api.types.is_datetime64_any_dtype(
        df["Date"]
    ):

        print(
            " -- La columna Date no está en formato de fecha --"
        )

        todo_correcto = False

    else:

        print(
            " -- Date tiene un tipo de dato adecuado --"
        )

    # 5. Fechas invlidas
    print("\n5. FECHAS")

    fechas_invalidas = df["Date"].isnull().sum()

    if fechas_invalidas == 0:

        print(" -- Todas las fechas son validas --")

    else:

        print(
            f" -- Existen {fechas_invalidas} fechas invalidas --"
        )

        todo_correcto = False


    # Verificar fechas posteriores al día de ejecución

    fecha_actual = datetime.now().date()

    fechas_futuras = (
        df["Date"].dt.date > fecha_actual
    ).sum()

    if fechas_futuras == 0:

        print(
            " -- Todas las fechas son validas --"
        )

    else:

        print(
            f" -- Existen {fechas_futuras} fechas posteriores "
            "al día de ejecución --"
        )

        todo_correcto = False

    # 6. Goles negativos
    print("\n6. GOLES")

    columnas_goles = [
        "FTHG",
        "FTAG"
    ]

    goles_negativos = 0

    for columna in columnas_goles:

        if columna in df.columns:

            cantidad = (
                df[columna] < 0
            ).sum()

            goles_negativos += cantidad

            if cantidad > 0:

                print(
                    f"✗ {columna}: "
                    f"{cantidad} valores negativos."
                )

    if goles_negativos == 0:

        print(
            " -- No existen goles negativos --"
        )

    else:

        todo_correcto = False

    # 7. Resultados FTR
    print("\n7. CATEGORÍA FTR")

    if "FTR" in df.columns:

        valores_ftr = sorted(
            df["FTR"].dropna().unique()
        )

        print(
            "Valores encontrados:",
            valores_ftr
        )

        valores_validos = {
            "H",
            "D",
            "A"
        }

        valores_invalidos = (
            set(valores_ftr) -
            valores_validos
        )

        if not valores_invalidos:

            print(
                " -- Todos los valores de FTR son válidos --"
            )

        else:

            print(
                " -- Valores inválidos en FTR -- \n",
                valores_invalidos
            )

            todo_correcto = False

    # 8. Nombres de equipos vacíos
    print("\n8. EQUIPOS")

    columnas_equipos = [
        "HomeTeam",
        "AwayTeam"
    ]

    equipos_vacios = 0

    for columna in columnas_equipos:

        if columna in df.columns:

            cantidad = (
                df[columna]
                .isnull()
                .sum()
            )

            equipos_vacios += cantidad

    if equipos_vacios == 0:

        print(
            " -- No existen equipos faltantes --"
        )

    else:

        print(
            f" -- Existen {equipos_vacios} "
            "valores de equipo faltantes --"
        )

        todo_correcto = False

    # RESULTADO FINAL

    print("\n")
    print("*******************************************\n")

    if todo_correcto:

        print(
            " -- DATASET EN ORDEN -- "
        )

        print(
            "No se encontraron problemas "
            "en las verificaciones realizadas."
        )

        # Exportar dataset final
        carpeta_datos = (
            Path(__file__).resolve()
            .parents[2]
            / "Dataset"
            / "Dataset Limpio"
        )

        carpeta_datos.mkdir(
            parents=True,
            exist_ok=True
        )

        ruta_final = (
            carpeta_datos
            / "dataset_limpio_definitivo.xlsx"
        )

        df.to_excel(
            ruta_final,
            index=False
        )

        print(
            "\n -- Dataset final exportado en:"
        )

        print(ruta_final, end='')
        print(" --")


    else:

        print(
            " -- DATASET CON OBSERVACIONES --"
        )

        print(
            "Se encontraron elementos "
            "que requieren revisión."
        )

    print()

    return todo_correcto