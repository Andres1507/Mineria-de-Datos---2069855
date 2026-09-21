
import requests
from collections import Counter
from datetime import datetime
from pathlib import Path

def detectar_valores_faltantes(df):

    """
    Identificación de valores faltantes y recuperación de horas
    mediante la API de FotMob.

    Las equivalencias entre los nombres de los equipos se determinan
    por temporada utilizando los partidos de ambas fuentes.
    """

    # Determinar la temporada de cada partido

    def obtener_temporada(fecha):

        if fecha.month >= 8:
            return f"{fecha.year}-{fecha.year + 1}"
        else:
            return f"{fecha.year - 1}-{fecha.year}"

    df_temporal = df.copy()

    df_temporal["Temporada"] = (
        df_temporal["Date"]
        .apply(obtener_temporada)
    )

    # Identificar registros que no tienen hora
    registros_sin_hora = df_temporal[
        df_temporal["Time"].isnull()
    ].copy()

    cantidad_original = len(registros_sin_hora)

    print("\nPartidos sin hora:", cantidad_original)

    # Obtener las temporadas que tienen valores faltantes
    temporadas = sorted(
        registros_sin_hora["Temporada"].unique()
    )

    print("\nTemporadas con partidos sin hora:")

    for temporada in temporadas:

        cantidad = (
            registros_sin_hora["Temporada"] == temporada
        ).sum()

        print(
            f"{temporada}: {cantidad} partidos"
        )

    # Crear copia para recuperar las horas
    df_limpio = df.copy()

    horas_recuperadas = 0

    partidos_no_encontrados = []

    # Procesar cada temporada
    for temporada in temporadas:

        print("\n")
        print("*********************************")
        print("Temporada:", temporada)
        print("*********************************")
        temporada_fotmob = temporada.replace("-", "/")

        # Todos los partidos de la temporada del dataset
        registros_temporada = df_temporal[
            df_temporal["Temporada"] == temporada
        ].copy()

        registros_temporada["Fecha"] = (
            registros_temporada["Date"].dt.date
        )

        # Partidos que realmente necesitan recuperación
        registros_faltantes = registros_temporada[
            registros_temporada["Time"].isnull()
        ].copy()

        print(
            "\nPartidos con hora faltante:",
            len(registros_faltantes)
        )

        # Equipos del dataset
        equipos_dataset = sorted(
            set(registros_temporada["HomeTeam"]) |
            set(registros_temporada["AwayTeam"])
        )

        # Consultar FotMob
        url = (
            "https://www.fotmob.com/api/data/leagues"
            f"?id=87&season={temporada_fotmob}&ccode3=ESP"
        )

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        respuesta = requests.get(
            url,
            headers=headers
        )

        """print(
            "Código de respuesta:",
            respuesta.status_code
        )"""

        if respuesta.status_code != 200:

            print(
                "No se pudo obtener la información de esta temporada."
            )

            for _, partido in registros_faltantes.iterrows():

                partidos_no_encontrados.append({
                    "Temporada": temporada,
                    "Fecha": partido["Fecha"],
                    "Local": partido["HomeTeam"],
                    "Visitante": partido["AwayTeam"]
                })

            continue

        datos = respuesta.json()

        partidos = datos["fixtures"]["allMatches"]

        print(
            "Partidos obtenidos de FotMob:",
            len(partidos)
        )

        # Extraer partidos de FotMob
        partidos_fotmob = []

        for partido in partidos:

            fecha_hora = datetime.fromisoformat(
                partido["status"]["utcTime"].replace(
                    "Z",
                    "+00:00"
                )
            )

            partidos_fotmob.append({
                "Fecha": fecha_hora.date(),
                "Local": partido["home"]["name"],
                "Visitante": partido["away"]["name"],
                "Hora": fecha_hora.time()
            })

        # Equipos de FotMob
        equipos_fotmob = sorted(
            set(
                partido["Local"]
                for partido in partidos_fotmob
            ) |
            set(
                partido["Visitante"]
                for partido in partidos_fotmob
            )
        )

        # Equipos con nombres iguales
        equipos_comunes = (
            set(equipos_dataset) &
            set(equipos_fotmob)
        )

        equivalencias = {}

        for equipo in equipos_comunes:

            equivalencias[equipo] = equipo

        # Buscar equivalencias mediante los partidos
        equipos_no_coinciden = (
            set(equipos_dataset) -
            set(equipos_fotmob)
        )

        print()
        for equipo_dataset in sorted(
            equipos_no_coinciden):

            candidatos = []

            partidos_dataset_equipo = registros_temporada[
                (
                    registros_temporada["HomeTeam"]
                    == equipo_dataset
                )
                |
                (
                    registros_temporada["AwayTeam"]
                    == equipo_dataset
                )
            ]

            
            for _, partido_dataset in (
                partidos_dataset_equipo.iterrows()):

                fecha = partido_dataset["Fecha"]

                es_local = (
                    partido_dataset["HomeTeam"]
                    == equipo_dataset
                )

                if es_local:

                    equipo_oponente = (
                        partido_dataset["AwayTeam"]
                    )

                else:

                    equipo_oponente = (
                        partido_dataset["HomeTeam"]
                    )

                #El rival debe ser un equipo cuya equivalencia ya conocemos
                if equipo_oponente not in equivalencias:

                    continue

                nombre_oponente_fotmob = equivalencias[
                    equipo_oponente
                ]

                # Buscar el mismo partido en FotMob
                for partido_fotmob in partidos_fotmob:

                    if partido_fotmob["Fecha"] != fecha:

                        continue

                    if es_local:

                        if (
                            partido_fotmob["Visitante"]
                            == nombre_oponente_fotmob
                        ):

                            candidatos.append(
                                partido_fotmob["Local"]
                            )

                    else:

                        if (
                            partido_fotmob["Local"]
                            == nombre_oponente_fotmob
                        ):

                            candidatos.append(
                                partido_fotmob["Visitante"]
                            )

            # Determinar la equivalencia
            if candidatos:

                conteo = Counter(candidatos)

                candidato, cantidad = (
                    conteo.most_common(1)[0]
                )

                equivalencias[candidato] = equipo_dataset

                print(
                    f"{candidato} - {equipo_dataset}"
                    #f" ({cantidad} coincidencias)"
                )

            else:

                print(
                    f"{equipo_dataset} → "
                    "No se pudo determinar"
                )

        # Recuperar las horas faltantes
        encontrados_temporada = 0

        for indice, partido_dataset in (
            registros_faltantes.iterrows()):

            for partido_fotmob in partidos_fotmob:

                # Comprobar fecha
                if (
                    partido_dataset["Fecha"]
                    != partido_fotmob["Fecha"]
                ):

                    continue

                # Convertir los nombres de FotMob al formato de nuestro dataset
                local_dataset = equivalencias.get(
                    partido_fotmob["Local"]
                )

                visitante_dataset = equivalencias.get(
                    partido_fotmob["Visitante"]
                )

                # Comprobar que ambos equipos tengan equivalencia
                if (
                    local_dataset is None
                    or visitante_dataset is None
                ):

                    continue

                # Comprobar local y visitante
                if (
                    partido_dataset["HomeTeam"]
                    == local_dataset
                    and
                    partido_dataset["AwayTeam"]
                    == visitante_dataset
                ):

                    hora = partido_fotmob["Hora"]

                    # Guardar la hora recuperada
                    df_limpio.loc[
                        indice,
                        "Time"
                    ] = hora.strftime("%H:%M")

                    encontrados_temporada += 1
                    horas_recuperadas += 1

                    break

            else:

                partidos_no_encontrados.append({
                    "Temporada": temporada,
                    "Fecha": partido_dataset["Fecha"],
                    "Local": partido_dataset["HomeTeam"],
                    "Visitante": partido_dataset["AwayTeam"]
                })

        print(
            "\nHoras recuperadas en esta temporada:",
            encontrados_temporada
        )

        print(
            "Partidos no encontrados en esta temporada:",
            len(
                [
                    partido
                    for partido in partidos_no_encontrados
                    if partido["Temporada"] == temporada
                ]
            )
        )

    faltantes_restantes = (
        df_limpio["Time"].isnull().sum()
    )

    print("\n")
    print(" ----- RESULTADO FINAL -----\n")

    print(
        "\nValores faltantes originales:",
        cantidad_original
    )

    print(
        "Horas recuperadas:",
        horas_recuperadas
    )

    print(
        "Valores faltantes restantes:",
        faltantes_restantes
    )

    print(
        "Partidos no encontrados:",
        len(partidos_no_encontrados)
    )

    carpeta_datos = (
        Path(__file__).resolve().parent / "Datos"
    )

    carpeta_datos.mkdir(
        exist_ok=True
    )

    ruta_salida = (
        carpeta_datos
        / "dataset sin valores faltantes.xlsx"
    )

    df_limpio.to_excel(
        ruta_salida,
        index=False
    )

    print(
        "\nArchivo generado:"
    )

    print(
        ruta_salida
    )

    return df_limpio