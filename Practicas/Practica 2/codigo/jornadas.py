import pandas as pd
from pathlib import Path


# CRITERIOS DE DESEMPATE

def partidos_directos_completos(
    equipos_empatados,
    partidos_considerados
):
    """
    Comprueba si ya se han disputado los dos enfrentamientos
    entre cada pareja de equipos empatados

    La funcion devuelve True si están disponibles todos los enfrentamientos y False si todavía falta al menos un enfrentamiento.
    """

    if len(equipos_empatados) < 2:
        return False

    for i in range(len(equipos_empatados)):

        for j in range(i + 1, len(equipos_empatados)):

            equipo_1 = equipos_empatados[i]
            equipo_2 = equipos_empatados[j]

            enfrentamientos = partidos_considerados[
                (
                    (
                        (partidos_considerados["HomeTeam"] == equipo_1)
                        &
                        (partidos_considerados["AwayTeam"] == equipo_2)
                    )
                    |
                    (
                        (partidos_considerados["HomeTeam"] == equipo_2)
                        &
                        (partidos_considerados["AwayTeam"] == equipo_1)
                    )
                )
            ]

            if len(enfrentamientos) < 2:
                return False

    return True


def calcular_enfrentamientos_directos(
    equipos,
    partidos_considerados
):

    datos_directos = {}

    for equipo in equipos:

        puntos = 0
        goles_favor = 0
        goles_contra = 0

        for _, partido in partidos_considerados.iterrows():

            local = partido["HomeTeam"]
            visitante = partido["AwayTeam"]

            # El partido debe ser entre dos equipos pertenecientes al grupo empatado.
            if local not in equipos:
                continue

            if visitante not in equipos:
                continue

            # Equipo local.
            if local == equipo:

                goles_equipo = partido["FTHG"]
                goles_rival = partido["FTAG"]

            # Equipo visitante.
            elif visitante == equipo:

                goles_equipo = partido["FTAG"]
                goles_rival = partido["FTHG"]

            else:
                continue

            goles_favor += goles_equipo
            goles_contra += goles_rival

            if goles_equipo > goles_rival:

                puntos += 3

            elif goles_equipo == goles_rival:

                puntos += 1

        datos_directos[equipo] = {
            "PtsDirectos": puntos,
            "DGDirecta": (
                goles_favor
                -
                goles_contra
            ),
            "GFDirectos": goles_favor
        }

    return datos_directos


def dividir_grupo_por_valor(
    dataframe,
    columna
):

    grupos = []

    valores = sorted(
        dataframe[columna].unique(),
        reverse=True
    )

    for valor in valores:

        grupo = dataframe[
            dataframe[columna] == valor
        ]

        grupos.append(
            grupo["Equipo"].tolist()
        )

    return grupos


def dividir_por_criterios_generales(
    equipos,
    tabla_actual
):
    """
    Aplica los criterios generales de diferencia de goles y de goles a favor.
    Si ambos criterios siguen iguales, los equipos permanecen en el mismo grupo.
    """

    grupo = tabla_actual[
        tabla_actual["Equipo"].isin(equipos)
    ].copy()

    grupo = grupo.sort_values(
        by=[
            "DG",
            "GF"
        ],
        ascending=[
            False,
            False
        ],
        kind="mergesort"
    )

    grupos = []

    grupo_actual = []

    valor_anterior = None

    for _, fila in grupo.iterrows():

        valor_actual = (
            fila["DG"],
            fila["GF"]
        )

        if (
            valor_anterior is not None
            and
            valor_actual != valor_anterior
        ):

            grupos.append(
                grupo_actual
            )

            grupo_actual = []

        grupo_actual.append(
            fila["Equipo"]
        )

        valor_anterior = valor_actual

    if grupo_actual:

        grupos.append(
            grupo_actual
        )

    return grupos


def ordenar_grupo_por_desempate(
    equipos_empatados,
    tabla_actual,
    partidos_considerados
):
    """
    Resuelve un grupo de equipos empatados a puntos.

    Para dos equipos:

        1. Diferencia de goles particular.
        2. Diferencia de goles general.
        3. Goles a favor.

    Para tres o más equipos:

        1. Puntos en enfrentamientos directos.
        2. Diferencia de goles particular.
        3. Diferencia de goles general.
        4. Goles a favor.


    Si después de todos los criterios disponibles
    continúan empatados, permanecen en el mismo grupo.
    """


    if len(equipos_empatados) <= 1:

        return [
            equipos_empatados
        ]


    directos_disponibles = (
        partidos_directos_completos(
            equipos_empatados,
            partidos_considerados
        )
    )

    if len(equipos_empatados) == 2:


        if directos_disponibles:

            datos_directos = (
                calcular_enfrentamientos_directos(
                    equipos_empatados,
                    partidos_considerados
                )
            )

            tabla_directa = pd.DataFrame(
                [
                    {
                        "Equipo": equipo,
                        **datos_directos[equipo]
                    }
                    for equipo in equipos_empatados
                ]
            )

            grupos_directos = (
                dividir_grupo_por_valor(
                    tabla_directa,
                    "DGDirecta"
                )
            )

            if len(grupos_directos) > 1:

                return grupos_directos

        return dividir_por_criterios_generales(
            equipos_empatados,
            tabla_actual
        )


    if len(equipos_empatados) >= 3:


        if not directos_disponibles:

            return dividir_por_criterios_generales(
                equipos_empatados,
                tabla_actual
            )


        datos_directos = (
            calcular_enfrentamientos_directos(
                equipos_empatados,
                partidos_considerados
            )
        )

        mini_tabla = pd.DataFrame(
            [
                {
                    "Equipo": equipo,
                    **datos_directos[equipo]
                }
                for equipo in equipos_empatados
            ]
        )

        grupos_por_puntos = (
            dividir_grupo_por_valor(
                mini_tabla,
                "PtsDirectos"
            )
        )

        resultado = []

        for grupo in grupos_por_puntos:

            if len(grupo) == 1:

                resultado.append(
                    grupo
                )

                continue

            grupos_subgrupo = (
                ordenar_grupo_por_desempate(
                    grupo,
                    tabla_actual,
                    partidos_considerados
                )
            )

            resultado.extend(
                grupos_subgrupo
            )

        return resultado

    return [
        equipos_empatados
    ]


def ordenar_clasificacion(
    tabla_actual,
    partidos_considerados
):

    grupos_finales = []

    puntos_diferentes = sorted(
        tabla_actual["Pts"].unique(),
        reverse=True
    )

    for puntos in puntos_diferentes:

        grupo = tabla_actual[
            tabla_actual["Pts"] == puntos
        ].copy()

        equipos = (
            grupo["Equipo"].tolist()
        )

        if len(equipos) == 1:

            grupos_finales.append(
                equipos
            )

            continue

        grupos_desempate = (
            ordenar_grupo_por_desempate(
                equipos,
                tabla_actual,
                partidos_considerados
            )
        )

        grupos_finales.extend(
            grupos_desempate
        )

    filas = []

    for grupo in grupos_finales:

        for equipo in grupo:

            fila = tabla_actual[
                tabla_actual["Equipo"] == equipo
            ].iloc[0].copy()

            filas.append(
                fila
            )

    tabla_ordenada = pd.DataFrame(
        filas
    ).reset_index(drop=True)


    posiciones = []

    posicion_actual = 1

    for grupo in grupos_finales:

        posiciones.extend(
            [posicion_actual] * len(grupo)
        )

        posicion_actual += len(grupo)

    tabla_ordenada.insert(
        0,
        "Pos",
        posiciones
    )

    return tabla_ordenada




# OBTENER CLASIFICACIONES FINALES DE TODAS LAS TEMPORADAS

def obtener_clasificaciones_finales():
    """
    Obtiene la clasificación final de cada una de las temporadas
    del dataset.

    Retorna:

        lista_clasificaciones:
            Lista de diccionarios, donde cada elemento contiene:

            - numero: número de temporada
            - nombre: nombre de la temporada
            - tabla_final: DataFrame con la clasificación final
    """

    ruta_dataset = (
        Path(__file__).resolve().parents[2]
        / "Dataset"
        / "Dataset Limpio"
        / "dataset_limpio_definitivo.xlsx"
    )

    df = pd.read_excel(
        ruta_dataset
    )

    partidos_por_temporada = 380
    total_partidos = len(df)

    if total_partidos % partidos_por_temporada != 0:

        raise ValueError(
            f"El dataset tiene {total_partidos} partidos "
            f"y no es divisible entre {partidos_por_temporada}."
        )

    cantidad_temporadas = (
        total_partidos // partidos_por_temporada
    )


    lista_clasificaciones = []

    for numero in range(cantidad_temporadas):

        inicio = (
            numero * partidos_por_temporada
        )

        fin = (
            inicio + partidos_por_temporada
        )

        df_temporada = df.iloc[
            inicio:fin
        ].copy()


        fecha_inicio = pd.to_datetime(
            df_temporada.iloc[0]["Date"]
        )

        fecha_fin = pd.to_datetime(
            df_temporada.iloc[-1]["Date"]
        )

        nombre_temporada = (
            f"{fecha_inicio.year}-"
            f"{str(fecha_fin.year)[-2:]}"
        )

        equipos_locales = (
            df_temporada["HomeTeam"].unique()
        )

        equipos_visitantes = (
            df_temporada["AwayTeam"].unique()
        )

        equipos = sorted(
            set(equipos_locales)
            |
            set(equipos_visitantes)
        )


        partidos_por_equipo = {}

        for equipo in equipos:

            partidos_local = (
                df_temporada[
                    df_temporada["HomeTeam"] == equipo
                ].copy()
            )

            partidos_visitante = (
                df_temporada[
                    df_temporada["AwayTeam"] == equipo
                ].copy()
            )

            partidos_equipo = pd.concat(
                [
                    partidos_local,
                    partidos_visitante
                ]
            )

            partidos_equipo = (
                partidos_equipo
                .sort_values(
                    by=[
                        "Date",
                        "Time"
                    ]
                )
            )

            partidos_por_equipo[equipo] = (
                partidos_equipo
            )


        datos_tabla = []

        for equipo in equipos:

            partidos_equipo = (
                partidos_por_equipo[equipo]
            )

            puntos = 0

            victorias = 0
            empates = 0
            derrotas = 0

            goles_favor = 0
            goles_contra = 0

            # RECORRER LOS 38 PARTIDOS

            for _, partido in partidos_equipo.iterrows():

                if partido["HomeTeam"] == equipo:

                    goles_equipo = (
                        partido["FTHG"]
                    )

                    goles_rival = (
                        partido["FTAG"]
                    )

                else:

                    goles_equipo = (
                        partido["FTAG"]
                    )

                    goles_rival = (
                        partido["FTHG"]
                    )

                goles_favor += goles_equipo
                goles_contra += goles_rival

                # VICTORIA

                if goles_equipo > goles_rival:

                    victorias += 1
                    puntos += 3

                # EMPATE

                elif goles_equipo == goles_rival:

                    empates += 1
                    puntos += 1

                # DERROTA

                else:

                    derrotas += 1

            # GUARDAR 

            datos_tabla.append(
                {
                    "Equipo": equipo,
                    "PJ": 38,
                    "PG": victorias,
                    "PE": empates,
                    "PP": derrotas,
                    "GF": goles_favor,
                    "GC": goles_contra,
                    "DG": (
                        goles_favor
                        -
                        goles_contra
                    ),
                    "Pts": puntos
                }
            )

        tabla_final = pd.DataFrame(
            datos_tabla
        )

        indices_partidos = set()

        for equipo in equipos:

            partidos_equipo = (
                partidos_por_equipo[equipo]
            )

            indices_partidos.update(
                partidos_equipo.index
            )

        partidos_considerados = (
            df_temporada[
                df_temporada.index.isin(
                    indices_partidos
                )
            ].copy()
        )


        tabla_final = ordenar_clasificacion(
            tabla_final,
            partidos_considerados
        )


        lista_clasificaciones.append(
            {
                "numero": numero + 1,
                "nombre": nombre_temporada,
                "tabla_final": tabla_final
            }
        )

    return lista_clasificaciones




def analizar_equipos():
    """
    Selecciona una temporada, obtiene los 20 equipos, muestra sus partidos como local y visitante ordenados cronológicamente y genera las 38 tablas comparativas.

    Cada tabla representa los primeros N partidos jugados por cada equipo.

    Victoria = 3 puntos
    Empate = 1 punto
    Derrota = 0 puntos.

    Al finalizar:

        - Tabla final
        - Campeón
        - Subcampeón
        - Tres equipos descendidos
    """


    ruta_dataset = (
        Path(__file__).resolve().parents[2]
        / "Dataset"
        / "Dataset Limpio"
        / "dataset_limpio_definitivo.xlsx"
    )

    df = pd.read_excel(
        ruta_dataset
    )


    partidos_por_temporada = 380
    total_partidos = len(df)

    if (
        total_partidos
        %
        partidos_por_temporada
        != 0
    ):

        print(
            f"Error: el dataset tiene "
            f"{total_partidos} partidos "
            f"y no es divisible entre "
            f"{partidos_por_temporada}."
        )

        return

    cantidad_temporadas = (
        total_partidos
        //
        partidos_por_temporada
    )

    temporadas = []

    for numero in range(
        cantidad_temporadas
    ):

        inicio = (
            numero
            *
            partidos_por_temporada
        )

        fin = (
            inicio
            +
            partidos_por_temporada
        )

        temporada = df.iloc[
            inicio:fin
        ]

        fecha_inicio = pd.to_datetime(
            temporada.iloc[0]["Date"]
        )

        fecha_fin = pd.to_datetime(
            temporada.iloc[-1]["Date"]
        )

        nombre_temporada = (
            f"{fecha_inicio.year}-"
            f"{str(fecha_fin.year)[-2:]}"
        )

        temporadas.append(
            {
                "numero": numero + 1,
                "nombre": nombre_temporada,
                "inicio": inicio,
                "fin": fin
            }
        )


    print(
        "\nTemporadas disponibles:"
    )

    print(
        "-" * 50
    )

    for temporada in temporadas:

        print(
            f"{temporada['numero']:2}. "
            f"{temporada['nombre']}"
        )

    print(
        "-" * 50
    )


    while True:

        try:

            seleccion = int(
                input(
                    "\nSelecciona una temporada (1-15): "
                )
            )

            if (
                1
                <=
                seleccion
                <=
                cantidad_temporadas
            ):

                break

            print(
                f"Introduce un número entre 1 y "
                f"{cantidad_temporadas}."
            )

        except ValueError:

            print(
                "Introduce un número válido."
            )

    temporada_seleccionada = (
        temporadas[
            seleccion - 1
        ]
    )

    inicio = (
        temporada_seleccionada["inicio"]
    )

    fin = (
        temporada_seleccionada["fin"]
    )

    df_temporada = df.iloc[
        inicio:fin
    ].copy()

    nombre_temporada = (
        temporada_seleccionada["nombre"]
    )

    equipos_locales = (
        df_temporada[
            "HomeTeam"
        ].unique()
    )

    equipos_visitantes = (
        df_temporada[
            "AwayTeam"
        ].unique()
    )

    equipos = sorted(
        set(equipos_locales)
        |
        set(equipos_visitantes)
    )

    print(
        "\n" + "=" * 70
    )

    print(
        f"TEMPORADA {nombre_temporada}"
    )

    print(
        "=" * 70
    )

    print(
        f"\nEquipos detectados: "
        f"{len(equipos)}"
    )

    print(
        "-" * 70
    )

    for numero, equipo in enumerate(
        equipos,
        start=1
    ):

        print(
            f"{numero:2}. {equipo}"
        )

    print(
        "=" * 70
    )


    partidos_por_equipo = {}

    for equipo in equipos:

        partidos_local = (
            df_temporada[
                df_temporada[
                    "HomeTeam"
                ]
                ==
                equipo
            ].copy()
        )

        partidos_visitante = (
            df_temporada[
                df_temporada[
                    "AwayTeam"
                ]
                ==
                equipo
            ].copy()
        )

        partidos_equipo = pd.concat(
            [
                partidos_local,
                partidos_visitante
            ]
        )

        partidos_equipo = (
            partidos_equipo
            .sort_values(
                by=[
                    "Date",
                    "Time"
                ]
            )
        )

        partidos_por_equipo[
            equipo
        ] = partidos_equipo


        print(
            "\n" + "-" * 70
        )

        print(
            f"Equipo: {equipo}"
        )

        print(
            "-" * 70
        )

        print(
            f"Partidos como local: "
            f"{len(partidos_local)}"
        )

        print(
            f"Partidos como visitante: "
            f"{len(partidos_visitante)}"
        )

        print(
            f"Partidos de este equipo: "
            f"{len(partidos_equipo)}"
        )

        if (
            len(partidos_local) == 19
            and
            len(partidos_visitante) == 19
        ):

            print(
                " 19 partidos como local "
                "y 19 como visitante."
            )

        else:

            print(
                " ERROR: distribución de "
                "partidos incorrecta."
            )

        print(
            "\nPartidos ordenados por fecha:"
        )

        for numero_partido, (
            _,
            partido
        ) in enumerate(
            partidos_equipo.iterrows(),
            start=1
        ):

            if (
                partido["HomeTeam"]
                ==
                equipo
            ):

                rival = (
                    partido["AwayTeam"]
                )

                condicion = "LOCAL"

            else:

                rival = (
                    partido["HomeTeam"]
                )

                condicion = "VISITANTE"

            print(
                f"{numero_partido:2}. "
                f"{partido['Date']} | "
                f"{partido['Time']} | "
                f"{condicion:10} | "
                f"{equipo} "
                f"{partido['FTHG']}-"
                f"{partido['FTAG']} "
                f"{rival}"
            )

    print(
        "\n\n"
    )

    print(
        "=" * 100
    )

    print(
        f"TABLAS COMPARATIVAS - "
        f"TEMPORADA {nombre_temporada}"
    )

    print(
        "=" * 100
    )

    tablas = []


    for numero_partido in range(
        1,
        39
    ):

        datos_tabla = []


        for equipo in equipos:

            partidos_equipo = (
                partidos_por_equipo[
                    equipo
                ]
            )

            primeros_partidos = (
                partidos_equipo.iloc[
                    :numero_partido
                ]
            )

            puntos = 0

            victorias = 0
            empates = 0
            derrotas = 0

            goles_favor = 0
            goles_contra = 0


            for _, partido in (
                primeros_partidos.iterrows()
            ):

                if (
                    partido["HomeTeam"]
                    ==
                    equipo
                ):

                    goles_equipo = (
                        partido["FTHG"]
                    )

                    goles_rival = (
                        partido["FTAG"]
                    )

                else:

                    goles_equipo = (
                        partido["FTAG"]
                    )

                    goles_rival = (
                        partido["FTHG"]
                    )

                goles_favor += (
                    goles_equipo
                )

                goles_contra += (
                    goles_rival
                )

                # VICTORIA

                if (
                    goles_equipo
                    >
                    goles_rival
                ):

                    victorias += 1
                    puntos += 3

                # EMPATE

                elif (
                    goles_equipo
                    ==
                    goles_rival
                ):

                    empates += 1
                    puntos += 1

                # DERROTA

                else:

                    derrotas += 1

            # GUARDAR DATOS DEL EQUIPO

            datos_tabla.append(
                {
                    "Equipo": equipo,
                    "PJ": numero_partido,
                    "PG": victorias,
                    "PE": empates,
                    "PP": derrotas,
                    "GF": goles_favor,
                    "GC": goles_contra,
                    "DG": (
                        goles_favor
                        -
                        goles_contra
                    ),
                    "Pts": puntos
                }
            )

        tabla = pd.DataFrame(
            datos_tabla
        )


        indices_partidos = set()

        for equipo in equipos:

            partidos_equipo = (
                partidos_por_equipo[
                    equipo
                ]
            )

            primeros_partidos = (
                partidos_equipo.iloc[
                    :numero_partido
                ]
            )

            indices_partidos.update(
                primeros_partidos.index
            )

        partidos_considerados = (
            df_temporada[
                df_temporada.index.isin(
                    indices_partidos
                )
            ].copy()
        )


        tabla = ordenar_clasificacion(
            tabla,
            partidos_considerados
        )

        tablas.append(
            tabla
        )

        print(
            "\n"
        )

        print(
            "=" * 100
        )

        print(
            f"TABLA DESPUÉS DE LOS PRIMEROS "
            f"{numero_partido} PARTIDOS "
            f"DE CADA CLUB"
        )


        print(
            "=" * 100
        )

        print(
            tabla.to_string(
                index=False
            )
        )

    # TABLA FINAL
    tabla_final = tablas[-1].copy()

    print(
        "\n\n"
    )

    print(
        "=" * 100
    )

    print(
        f"TABLA FINAL - TEMPORADA "
        f"{nombre_temporada}"
    )

    print(
        "=" * 100
    )

    print(
        tabla_final.to_string(
            index=False
        )
    )

    print(
        "\n"
    )

    print(
        "=" * 100
    )

    print(
        f"RESUMEN DE LA TEMPORADA "
        f"{nombre_temporada}"
    )

    print(
        "=" * 100
    )

    # CAMPEÓN

    campeon = tabla_final[
        tabla_final["Pos"] == 1
    ]

    if len(campeon) == 1:

        fila = campeon.iloc[0]

        print(
            f"\nCAMPEÓN: "
            f"{fila['Equipo']}"
        )

        print(
            f"   Puntos: "
            f"{int(fila['Pts'])}"
        )

    else:

        print(
            "\nCAMPEÓN: "
            "No se puede determinar "
            "de forma única."
        )

        for _, fila in campeon.iterrows():

            print(
                f"   - {fila['Equipo']}"
            )

    # SUBCAMPEÓN

    subcampeon = tabla_final[
        tabla_final["Pos"] == 2
    ]

    if len(subcampeon) == 1:

        fila = subcampeon.iloc[0]

        print(
            f"\nSUBCAMPEÓN: "
            f"{fila['Equipo']}"
        )

        print(
            f"   Puntos: "
            f"{int(fila['Pts'])}"
        )

    else:

        print(
            "\nSUBCAMPEÓN: "
            "No se puede determinar "
            "de forma única."
        )

        for _, fila in subcampeon.iterrows():

            print(
                f"   - {fila['Equipo']}"
            )

    # DESCENDIDOS

    descendidos = tabla_final[
        tabla_final["Pos"].isin(
            [18, 19, 20]
        )
    ].copy()

    print(
        "\nDESCENDIDOS A SEGUNDA DIVISIÓN:"
    )

    if len(descendidos) == 3:

        descendidos = descendidos.sort_values(
            by="Pos"
        )

        for _, fila in descendidos.iterrows():

            print(
                f"   {int(fila['Pos'])}. "
                f"{fila['Equipo']} "
                f"({int(fila['Pts'])} pts)"
            )

    else:

        print(
            "   No se pueden determinar "
            "de forma completamente única "
            "las tres posiciones de descenso."
        )

        descendidos = descendidos.sort_values(
            by="Pos"
        )

        for _, fila in descendidos.iterrows():

            print(
                f"   {int(fila['Pos'])}. "
                f"{fila['Equipo']} "
                f"({int(fila['Pts'])} pts)"
            )

    print(
        "\n"
        + "=" * 100
    )

    return tablas



if __name__ == "__main__":

    analizar_equipos()