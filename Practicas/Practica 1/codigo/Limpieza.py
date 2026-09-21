"""
Limpieza de Datos

Se realizará el proceso de limpieza de datos para un conjunto de información
relacionada con la Liga Española de Fútbol en su Primera División, donde cada
registro representa un partido e incluye variables referentes a la fecha y
hora del encuentro, equipos local y visitante, resultado final y estadísticas
del encuentro, con el fin de dejar el conjunto de datos disponible y listo
para su posterior tratamiento y análisis.

"""

from cargar_datos import cargar_datos
from duplicados import detectar_duplicados
from valores_faltantes import detectar_valores_faltantes
from verificar import verificar_dataset
from ordenar import ordenar_por_fecha_hora


def main():


    df = cargar_datos()





    print("\n")
    print("=================================================")
    print("Deteccion y Eliminacion De Registros Duplicados")
    print("================================================\n")

    df_sin = detectar_duplicados(df)





    print("\n")
    print("===================================")
    print("Obtencion de elementos faltantes")
    print("==================================\n")

    df_completo = detectar_valores_faltantes(df_sin)




    print("\n")
    print("===================")
    print("Ordenar DataSet")
    print("==================\n")

    df_ordenado = ordenar_por_fecha_hora(df_completo)




    print("\n")
    print("=============================================")
    print("Verificacion de la integridad de los datos")
    print("===========================================\n")

    verificar_dataset(df_ordenado)

   


if __name__ == "__main__":
    main()
    input()