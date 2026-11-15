
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# RUTAS
BASE_DIR = Path(__file__).resolve().parents[1]
RUTA_DATOS = BASE_DIR / "doc" / "resultados" / "06 - Prediccion 2026-27.xlsx"
RUTA_RESULTADOS = BASE_DIR / "doc" / "resultados"

# CARGAR DATOS
df = pd.read_excel(RUTA_DATOS, sheet_name="Predicciones")

modelos = [
    "E0 - Extrapolacion",
    "E1 - Regresion simple",
    "E2 - Regresion multiple"
]

datos = df.pivot(
    index="Equipo",
    columns="Modelo",
    values="PuntosEstimados"
)

# ORDENAR EQUIPOS SEGUN E2
datos = datos.sort_values(
    "E2 - Regresion multiple",
    ascending=True
)

# GRAFICA 1: PUNTOS ESTIMADOS
ax = datos[modelos].plot(
    kind="barh",
    figsize=(12, 9),
    width=0.8
)

ax.set_title("Puntos finales estimados por modelo")
ax.set_xlabel("Puntos estimados")
ax.set_ylabel("Equipo")
ax.grid(axis="x", linestyle="--", alpha=0.4)
ax.legend(title="Modelo")
plt.tight_layout()

plt.savefig(
    RUTA_RESULTADOS / "07 - Puntos estimados 2026-27.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()
print("GRAFICA 1 GENERADA CORRECTAMENTE")


# GRAFICA 2: POSICIONES PROYECTADAS
posiciones = df.pivot(
    index="Equipo",
    columns="Modelo",
    values="PosicionPredicha"
)

posiciones = posiciones.loc[datos.index]

plt.figure(figsize=(13, 7))

for modelo in modelos:
    plt.plot(
        posiciones.index,
        posiciones[modelo],
        marker="o",
        linewidth=1.8,
        label=modelo
    )

plt.title("Comparación de posiciones proyectadas por modelo")
plt.xlabel("Equipo")
plt.ylabel("Posición estimada")
plt.yticks(range(1, 21))
plt.gca().invert_yaxis()
plt.xticks(rotation=75, ha="right")
plt.grid(axis="y", linestyle="--", alpha=0.4)
plt.legend(title="Modelo")
plt.tight_layout()

plt.savefig(
    RUTA_RESULTADOS / "07 - Posiciones proyectadas 2026-27.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()
print("GRAFICA 2 GENERADA CORRECTAMENTE")



