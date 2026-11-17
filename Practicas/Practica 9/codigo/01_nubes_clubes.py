from pathlib import Path
import importlib.util
from collections import Counter
import sys

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from wordcloud import WordCloud


#RUTAS 
CARPETA_CODIGO = Path(__file__).resolve().parent
CARPETA_PRACTICA = CARPETA_CODIGO.parent
RAIZ_PROYECTO = CARPETA_PRACTICA.parent

RUTA_DATASET = (
    RAIZ_PROYECTO
    / 'Dataset'
    / 'Dataset Limpio'
    / 'dataset_limpio_definitivo.xlsx'
)

RUTA_JORNADAS = (
    RAIZ_PROYECTO
    / 'Practica 2'
    / 'codigo'
    / 'jornadas.py'
)

CARPETA_RESULTADOS = CARPETA_PRACTICA / 'doc' / 'resultados'
CARPETA_RESULTADOS.mkdir(parents=True, exist_ok=True)

if not RUTA_DATASET.exists():
    raise FileNotFoundError(f'No se encontro el dataset: {RUTA_DATASET}')

if not RUTA_JORNADAS.exists():
    raise FileNotFoundError(f'No se encontro jornadas.py: {RUTA_JORNADAS}')


#CARGAR EL MODULO DE CLASIFICACIONES
spec = importlib.util.spec_from_file_location('jornadas', RUTA_JORNADAS)
jornadas = importlib.util.module_from_spec(spec)
sys.modules['jornadas'] = jornadas
spec.loader.exec_module(jornadas)

clasificaciones = jornadas.obtener_clasificaciones_finales()

if len(clasificaciones) != 15:
    raise ValueError(
        f'Se esperaban 15 temporadas y se encontraron {len(clasificaciones)}.'
    )


#DEFINIR LAS ZONAS 

ZONAS = {
    'Campeones': (1, 1),
    'Zona alta': (2, 6),
    'Zona media': (7, 15),
    'Zona baja': (16, 17),
    'Descendidos': (18, 20),
}

ALIAS = {
    'Alaves': 'Alavés',
    'Almeria': 'Almería',
    'Ath Bilbao': 'Athletic Club',
    'Ath Madrid': 'Atlético de Madrid',
    'Cordoba': 'Córdoba',
    'Espanol': 'Espanyol',
    'La Coruna': 'Deportivo de La Coruña',
    'Malaga': 'Málaga',
    'Santander': 'Racing de Santander',
    'Sociedad': 'Real Sociedad',
    'Sp Gijon': 'Sporting de Gijón',
    'Vallecano': 'Rayo Vallecano',
}


def obtener_zona(posicion):
    for nombre, (minimo, maximo) in ZONAS.items():
        if minimo <= posicion <= maximo:
            return nombre
    raise ValueError(f'Posicion fuera de rango: {posicion}')


#CONSTRUIR LOS 300 REGISTROS EQUIPO YTEMPORADA
registros = []

for temporada in clasificaciones:
    nombre_temporada = temporada['nombre']
    tabla = temporada['tabla_final']

    if len(tabla) != 20 or tabla['Pos'].nunique() != 20:
        raise ValueError(
            f'La clasificacion {nombre_temporada} no contiene 20 posiciones unicas.'
        )

    for _, fila in tabla.iterrows():
        equipo_original = str(fila['Equipo'])
        equipo = ALIAS.get(equipo_original, equipo_original)
        posicion = int(fila['Pos'])

        registros.append({
            'Temporada': nombre_temporada,
            'Equipo': equipo,
            'Equipo original': equipo_original,
            'Posicion final': posicion,
            'Puntos': int(fila['Pts']),
            'Zona competitiva': obtener_zona(posicion),
        })

participaciones = pd.DataFrame(registros)

if len(participaciones) != 300:
    raise ValueError(f'Se esperaban 300 registros y hay {len(participaciones)}.')


#CALCULAR FRECUENCIAS POR ZONA Y FRECUENCIA GENERAL
frecuencias = []
matriz = []
equipos = sorted(participaciones['Equipo'].unique())

for equipo in equipos:
    fila = {'Equipo': equipo}
    for zona in ZONAS:
        cantidad = int(
            ((participaciones['Equipo'] == equipo) &
             (participaciones['Zona competitiva'] == zona)).sum()
        )
        fila[zona] = cantidad
    fila['Total temporadas'] = int((participaciones['Equipo'] == equipo).sum())
    fila['% de temporadas'] = round(fila['Total temporadas'] / 15 * 100, 2)
    matriz.append(fila)

    for zona, (pos_min, pos_max) in ZONAS.items():
        cantidad = fila[zona]
        total_plazas = (pos_max - pos_min + 1) * 15
        frecuencias.append({
            'Zona competitiva': zona,
            'Posiciones': f'{pos_min}-{pos_max}' if pos_min != pos_max else str(pos_min),
            'Equipo': equipo,
            'Apariciones': cantidad,
            '% de plazas de la zona': round(cantidad / total_plazas * 100, 2),
            '% de temporadas': round(cantidad / 15 * 100, 2),
        })

frecuencias_zona = pd.DataFrame(frecuencias)
matriz_clubes = pd.DataFrame(matriz)

frecuencia_general = (
    participaciones.groupby('Equipo')
    .size()
    .reset_index(name='Temporadas participadas')
)
frecuencia_general['% de las 15 temporadas'] = (
    frecuencia_general['Temporadas participadas'] / 15 * 100
).round(2)
frecuencia_general = frecuencia_general.sort_values(
    ['Temporadas participadas', 'Equipo'], ascending=[False, True]
).reset_index(drop=True)


#RESUMEN DE LAS ZONAS
resumen = []
for zona, (pos_min, pos_max) in ZONAS.items():
    subset = frecuencias_zona[frecuencias_zona['Zona competitiva'] == zona]
    subset = subset[subset['Apariciones'] > 0].sort_values(
        ['Apariciones', 'Equipo'], ascending=[False, True]
    )
    total_plazas = (pos_max - pos_min + 1) * 15
    total_apariciones = int(subset['Apariciones'].sum())
    top1 = int(subset.iloc[0]['Apariciones']) if len(subset) else 0
    top3 = int(subset.head(3)['Apariciones'].sum()) if len(subset) else 0
    resumen.append({
        'Zona competitiva': zona,
        'Posiciones': f'{pos_min}-{pos_max}' if pos_min != pos_max else str(pos_min),
        'Plazas historicas': total_plazas,
        'Clubes distintos': int(len(subset)),
        'Club mas frecuente': subset.iloc[0]['Equipo'] if len(subset) else '',
        'Apariciones del lider': top1,
        '% de plazas del lider': round(top1 / total_plazas * 100, 2),
        'Apariciones Top 3 clubes': top3,
        '% de plazas Top 3': round(top3 / total_plazas * 100, 2),
    })

resumen_zonas = pd.DataFrame(resumen)


#GENERAR NUBES DE PALABRAS
CONFIG_CLOUDS = [
    ('General', 'Nube general - presencia historica de clubes',
     dict(zip(frecuencia_general['Equipo'], frecuencia_general['Temporadas participadas'])), 'viridis'),
]

COLORMAPS = {
    'Campeones': 'YlOrBr',
    'Zona alta': 'Blues',
    'Zona media': 'Greens',
    'Zona baja': 'Oranges',
    'Descendidos': 'Reds',
}

for zona in ZONAS:
    sub = frecuencias_zona[
        (frecuencias_zona['Zona competitiva'] == zona) &
        (frecuencias_zona['Apariciones'] > 0)
    ]
    diccionario = dict(zip(sub['Equipo'], sub['Apariciones']))
    CONFIG_CLOUDS.append((zona, f'Nube de clubes - {zona.lower()}', diccionario, COLORMAPS[zona]))

for clave, titulo, frecuencias_cloud, mapa in CONFIG_CLOUDS:
    if not frecuencias_cloud:
        continue

    cmap_base = plt.get_cmap(mapa)
    cmap_recortado = LinearSegmentedColormap.from_list(
        f'{mapa}_legible', cmap_base([0.32, 0.48, 0.64, 0.80, 0.94])
    )

    nube = WordCloud(
        width=1800,
        height=1100,
        background_color='white',
        colormap=cmap_recortado,
        prefer_horizontal=1.0,
        collocations=False,
        normalize_plurals=False,
        margin=18,
        max_words=50,
        min_font_size=20,
        max_font_size=220,
        relative_scaling=0.55,
        random_state=42,
    ).generate_from_frequencies(frecuencias_cloud)

    fig, ax = plt.subplots(figsize=(16, 10), dpi=150)
    ax.imshow(nube, interpolation='bilinear')
    ax.axis('off')
    ax.set_title(titulo, fontsize=24, weight='bold', pad=22)

    if clave == 'General':
        subtitulo = 'Frecuencia: temporadas participadas (maximo 15)'
        nombre_archivo = '02 - Nube general - clubes.png'
    else:
        pos_min, pos_max = ZONAS[clave]
        tramo = f'{pos_min}' if pos_min == pos_max else f'{pos_min}o-{pos_max}o'
        subtitulo = f'Frecuencia: temporadas en posiciones {pos_min}.º–{pos_max}.º'
        nombre_archivo = f'03 - Nube de clubes - {clave.lower()}.png'

    fig.text(0.5, 0.035, subtitulo, ha='center', fontsize=13, color='#555555')
    fig.tight_layout(rect=[0.02, 0.06, 0.98, 0.94])
    fig.savefig(CARPETA_RESULTADOS / nombre_archivo, bbox_inches='tight', facecolor='white')
    plt.close(fig)


#GRAFICA: TOP 10 POR ZONA
fig, axes = plt.subplots(2, 3, figsize=(22, 13), dpi=150)
axes = axes.flatten()

for i, zona in enumerate(ZONAS):
    ax = axes[i]
    sub = frecuencias_zona[
        (frecuencias_zona['Zona competitiva'] == zona) &
        (frecuencias_zona['Apariciones'] > 0)
    ].sort_values(['Apariciones', 'Equipo'], ascending=[True, True]).tail(10)
    pos_min, pos_max = ZONAS[zona]
    top = int(sub['Apariciones'].max()) if len(sub) else 1
    ax.barh(sub['Equipo'], sub['Apariciones'], color=plt.get_cmap(COLORMAPS[zona])(0.65))
    ax.set_title(zona, fontsize=16, weight='bold')
    ax.set_xlabel('Temporadas en la zona')
    ax.set_xlim(0, max(top + 1, 2))
    ax.grid(axis='x', alpha=0.2)
    ax.set_axisbelow(True)

ax = axes[5]
sub = frecuencia_general.sort_values(
    ['Temporadas participadas', 'Equipo'], ascending=[True, True]
).tail(10)
ax.barh(sub['Equipo'], sub['Temporadas participadas'], color=plt.get_cmap('viridis')(0.65))
ax.set_title('Presencia histórica total (Top 10)', fontsize=16, weight='bold')
ax.set_xlabel('Temporadas participadas')
ax.set_xlim(0, 16)
ax.grid(axis='x', alpha=0.2)
ax.set_axisbelow(True)

fig.suptitle('Frecuencia de clubes por contexto competitivo', fontsize=22, weight='bold')
fig.tight_layout(rect=[0, 0, 1, 0.96])
fig.savefig(CARPETA_RESULTADOS / '08 - Frecuencia de clubes por zona.png', bbox_inches='tight', facecolor='white')
plt.close(fig)


#EXPORTAR TABLAS CSV 
participaciones.to_csv(
    CARPETA_RESULTADOS / 'participaciones_equipo_temporada.csv',
    index=False,
    encoding='utf-8-sig'
)
frecuencias_zona.to_csv(
    CARPETA_RESULTADOS / 'frecuencias_clubes_por_zona.csv',
    index=False,
    encoding='utf-8-sig'
)
matriz_clubes.to_csv(
    CARPETA_RESULTADOS / 'matriz_clubes_zonas.csv',
    index=False,
    encoding='utf-8-sig'
)
frecuencia_general.to_csv(
    CARPETA_RESULTADOS / 'frecuencia_general_clubes.csv',
    index=False,
    encoding='utf-8-sig'
)
resumen_zonas.to_csv(
    CARPETA_RESULTADOS / 'resumen_zonas.csv',
    index=False,
    encoding='utf-8-sig'
)

print('Analisis terminado correctamente.')
print(f'Temporadas: {len(clasificaciones)}')
print(f'Registros equipo-temporada: {len(participaciones)}')
print(f'Clubes distintos: {participaciones["Equipo"].nunique()}')
print(f'Resultados: {CARPETA_RESULTADOS}')
print('\nFrecuencias principales:')
print(resumen_zonas.to_string(index=False))
