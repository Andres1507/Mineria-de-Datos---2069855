import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from scipy.stats import spearmanr

# RUTAS
BASE_DIR = Path(__file__).resolve().parents[1]
RUTA_DATOS = BASE_DIR / "doc" / "resultados" / "04 - Predictibilidad y Competitividad.xlsx"
RUTA_RESULTADOS = BASE_DIR / "doc" / "resultados"

# CARGAR DATOS
df = pd.read_excel(RUTA_DATOS, sheet_name="Resumen general")

# PREPARAR DATOS
datos = df.pivot(
    index="PartidosDisputados",
    columns="Modelo",
    values="MAE_Puntos_Promedio"
)

# GRAFICA 1: EVOLUCION DEL ERROR
plt.figure(figsize=(11, 6))

for modelo in datos.columns:
    plt.plot(
        datos.index,
        datos[modelo],
        marker="o",
        linewidth=2,
        markersize=6,
        label=modelo
    )

plt.title("Evolución del error de predicción durante la temporada")
plt.xlabel("Partidos disputados")
plt.ylabel("Error absoluto medio (MAE) en puntos")
plt.xticks(datos.index)
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.legend(title="Modelo")
plt.tight_layout()

plt.savefig(
    RUTA_RESULTADOS / "05 - Evolucion del error de prediccion.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

print("GRAFICA 1 GENERADA CORRECTAMENTE")




# GRAFICA 2: VENTAJA DE LOS MODELOS DE REGRESION
modelo_e0 = next(c for c in datos.columns if c.startswith("E0"))
modelo_e1 = next(c for c in datos.columns if c.startswith("E1"))
modelo_e2 = next(c for c in datos.columns if c.startswith("E2"))

ventaja_e1 = datos[modelo_e0] - datos[modelo_e1]
ventaja_e2 = datos[modelo_e0] - datos[modelo_e2]

plt.figure(figsize=(11, 6))

plt.plot(
    datos.index, ventaja_e1,
    marker="o", linewidth=2,
    label="E1 - Regresión simple"
)

plt.plot(
    datos.index, ventaja_e2,
    marker="o", linewidth=2,
    label="E2 - Regresión múltiple"
)

plt.axhline(0, color="gray", linestyle="--", linewidth=1)

plt.title("Ventaja de los modelos de regresión frente a la extrapolación")
plt.xlabel("Partidos disputados")
plt.ylabel("Reducción del MAE respecto a E0 (puntos)")
plt.xticks(datos.index)
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.legend()
plt.tight_layout()

plt.savefig(
    RUTA_RESULTADOS / "05 - Ventaja de los modelos de regresion.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

print("GRAFICA 2 GENERADA CORRECTAMENTE")





# GRAFICA 3: DISPERSION DE PUNTOS Y ERROR DE PREDICCION

errores = pd.read_excel(RUTA_DATOS, sheet_name="Errores por temporada")

modelo = errores["Modelo"].str.startswith("E2")
cortes = [5, 19, 25]

fig, axes = plt.subplots(
    3, 1,
    figsize=(10, 14),
    sharey=True
)

for ax, corte in zip(axes, cortes):
    datos_corte = errores[
        modelo & (errores["PartidosDisputados"] == corte)
    ].dropna(subset=["DesvEstandar", "MAE_Puntos"])

    x = datos_corte["DesvEstandar"].to_numpy()
    y = datos_corte["MAE_Puntos"].to_numpy()

    ax.scatter(x, y, s=65, alpha=0.8)

    pendiente, intercepto = np.polyfit(x, y, 1)
    valores_x = np.linspace(x.min(), x.max(), 100)

    ax.plot(
        valores_x,
        pendiente * valores_x + intercepto,
        linestyle="--",
        linewidth=1.5
    )

    rho, p = spearmanr(x, y)

    ax.set_title(f"{corte} partidos | Spearman: {rho:.2f}", pad=10)
    ax.set_xlabel("Desviación estándar de puntos")
    ax.set_ylabel("MAE de puntos")
    ax.grid(alpha=0.3, linestyle="--")

fig.suptitle(
    "RELACIÓN ENTRE DISPERSIÓN COMPETITIVA Y ERROR DE PREDICCIÓN",
    fontsize=14,
    y=0.98
)

fig.subplots_adjust(
    top=0.92,
    bottom=0.06,
    hspace=0.85
)

plt.savefig(
    RUTA_RESULTADOS / "05 - Dispersion y error de prediccion.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()
print("GRAFICA 3 GENERADA CORRECTAMENTE")




# GRAFICA 4: MOVILIDAD Y ERROR DE PREDICCION

cortes = [5, 19, 25]

fig, axes = plt.subplots(
    3, 1,
    figsize=(10, 14),
    sharey=True
)

for ax, corte in zip(axes, cortes):
    datos_corte = errores[
        modelo & (errores["PartidosDisputados"] == corte)
    ].dropna(subset=["MovilidadPct", "MAE_Puntos"])

    x = datos_corte["MovilidadPct"].to_numpy()
    y = datos_corte["MAE_Puntos"].to_numpy()

    ax.scatter(x, y, s=65, alpha=0.8)

    pendiente, intercepto = np.polyfit(x, y, 1)
    valores_x = np.linspace(x.min(), x.max(), 100)

    ax.plot(
        valores_x,
        pendiente * valores_x + intercepto,
        linestyle="--",
        linewidth=1.5
    )

    rho, p = spearmanr(x, y)

    ax.set_title(f"{corte} partidos | Spearman: {rho:.2f}", pad=10)
    ax.set_xlabel("Movilidad entre zonas (%)")
    ax.set_ylabel("MAE de puntos")
    ax.grid(alpha=0.3, linestyle="--")

fig.suptitle(
    "RELACIÓN ENTRE MOVILIDAD COMPETITIVA Y ERROR DE PREDICCIÓN",
    fontsize=14,
    y=0.98
)

fig.subplots_adjust(
    top=0.92,
    bottom=0.06,
    hspace=0.85
)

plt.savefig(
    RUTA_RESULTADOS / "05 - Movilidad y error de prediccion.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()
print("GRAFICA 4 GENERADA CORRECTAMENTE")



