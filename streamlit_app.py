import math
import streamlit as st
import pandas as pd
st.set_page_config(page_title="Calculadora de Materiales (Demo)", layout="centered")

# -----------------------------
# Parámetros de demostración
# -----------------------------
BOLSA_CEMENTO_KG = 42.5

# Coeficientes base (placeholders ajustables)
# Concretos (por 1 m3 de concreto)
CONCRETO = {
    "cemento_kg_por_m3": 320.0,
    "arena_m3_por_m3": 0.50,
    "piedrin_m3_por_m3": 0.70,   # "piedrín" == "grava"
    "agua_l_por_m3": 180.0,
    "acero_kg_por_m3": 85.0,
}

CONCRETO_ESTRUCTURA = {
    # columnas/vigas pueden usar más acero
    "cemento_kg_por_m3": 340.0,
    "arena_m3_por_m3": 0.48,
    "piedrin_m3_por_m3": 0.72,
    "agua_l_por_m3": 185.0,
    "acero_kg_por_m3": 110.0,
}

CONCRETO_CIMIENTOS = {
    "cemento_kg_por_m3": 300.0,
    "arena_m3_por_m3": 0.50,
    "piedrin_m3_por_m3": 0.70,
    "agua_l_por_m3": 175.0,
    "acero_kg_por_m3": 40.0,
}

CONCRETO_CONTRAPISO = {
    "cemento_kg_por_m3": 280.0,
    "arena_m3_por_m3": 0.55,
    "piedrin_m3_por_m3": 0.65,
    "agua_l_por_m3": 170.0,
    "acero_kg_por_m3": 0.0,
}

# Muro de block (por m2 de muro)
MAMPOSTERIA = {
    "blocks_por_m2": 12.5,
    "mortero_cemento_kg_por_m2": 9.0,
    "mortero_arena_m3_por_m2": 0.018,
}

# Factores por departamento (demo)
K_FACTOR = {
    "Guatemala": {
        "losa": 1.00, "contrapiso": 1.00, "muro_block": 1.00, "cimientos": 1.00, "col_viga": 1.00
    },
    "Quetzaltenango": {
        "losa": 1.05, "contrapiso": 1.05, "muro_block": 1.08, "cimientos": 1.02, "col_viga": 1.06
    },
    "Petén": {
        "losa": 0.98, "contrapiso": 0.98, "muro_block": 0.95, "cimientos": 0.97, "col_viga": 0.96
    },
}

# Desperdicios por partida (demo)
WASTE = {
    "losa": 0.05,
    "contrapiso": 0.05,
    "muro_block": 0.07,
    "cimientos": 0.05,
    "col_viga": 0.05,
}

# Parámetros geométricos por defecto
ALTURA_MURO_M = 2.5
ESPESOR_LOSA_M = 0.12
ESPESOR_CONTRAPISO_M = 0.08
BASE_CIMIENTO_M = 0.50
ALTURA_CIMIENTO_M = 0.60

# Factores de volumetría cuando no hay layout (m3 por m2)
FACTOR_COL_M3_POR_M2 = 0.020
FACTOR_VIGA_M3_POR_M2 = 0.015

# -----------------------------
# Funciones
# -----------------------------
def estimar_perimetro(area_m2: float) -> float:
    # aproximación: planta casi cuadrada
    lado = math.sqrt(max(area_m2, 1e-6))
    return lado * 4.0

def aplicar_waste(x: float, waste: float) -> float:
    return x * (1.0 + waste)

def kf(depto: str, partida: str) -> float:
    return K_FACTOR.get(depto, {}).get(partida, 1.0)

# -----------------------------
# UI
# -----------------------------
st.title("Calculadora de Materiales (Demo)")
st.caption("Prototipo para validación — cantidades aproximadas con supuestos editables.")

col1, col2, col3 = st.columns(3)
with col1:
    depto = st.selectbox("Departamento", list(K_FACTOR.keys()), index=0)
with col2:
    niveles = st.selectbox("Niveles", [1, 2, 3], index=1)
with col3:
    area_m2_total = st.number_input("Área construida total (m²)", min_value=20.0, max_value=1000.0, value=120.0, step=5.0)

st.markdown("---")
st.subheader("Suposiciones geométricas")
with st.expander("Editar parámetros (opcional)"):
    altura_muro_m = st.number_input("Altura de muro (m)", min_value=2.2, max_value=3.2, value=ALTURA_MURO_M, step=0.1)
    espesor_losa_m = st.number_input("Espesor losa (m)", min_value=0.08, max_value=0.20, value=ESPESOR_LOSA_M, step=0.01)
    espesor_contrapiso_m = st.number_input("Espesor contrapiso (m)", min_value=0.05, max_value=0.12, value=ESPESOR_CONTRAPISO_M, step=0.005)
    base_cimiento_m = st.number_input("Base cimiento corrido (m)", min_value=0.30, max_value=0.80, value=BASE_CIMIENTO_M, step=0.05)
    altura_cimiento_m = st.number_input("Altura cimiento corrido (m)", min_value=0.40, max_value=0.80, value=ALTURA_CIMIENTO_M, step=0.05)
    factor_col_m3_por_m2 = st.number_input("Factor columnas (m³ por m²)", min_value=0.005, max_value=0.05, value=FACTOR_COL_M3_POR_M2, step=0.001, format="%.3f")
    factor_viga_m3_por_m2 = st.number_input("Factor vigas (m³ por m²)", min_value=0.005, max_value=0.05, value=FACTOR_VIGA_M3_POR_M2, step=0.001, format="%.3f")

# -----------------------------
# Cálculo por partida
# -----------------------------
m2_por_nivel = area_m2_total / niveles
perimetro_m = estimar_perimetro(m2_por_nivel)  # por nivel

# Losa (m3)
losa_m3 = m2_por_nivel * espesor_losa_m * niveles
losa_m3 *= kf(depto, "losa")
losa_m3 = aplicar_waste(losa_m3, WASTE["losa"])

# Contrapiso (m3)
contrapiso_m3 = area_m2_total * espesor_contrapiso_m
contrapiso_m3 *= kf(depto, "contrapiso")
contrapiso_m3 = aplicar_waste(contrapiso_m3, WASTE["contrapiso"])

# Muros de block
muro_m2 = perimetro_m * altura_muro_m * niveles
muro_m2 *= kf(depto, "muro_block")
muro_m2 = aplicar_waste(muro_m2, WASTE["muro_block"])

# Cimientos corridos (m3)
cimientos_m3 = perimetro_m * base_cimiento_m * altura_cimiento_m
cimientos_m3 *= kf(depto, "cimientos")
cimientos_m3 = aplicar_waste(cimientos_m3, WASTE["cimientos"])

# Columnas + Vigas (m3)
col_m3 = factor_col_m3_por_m2 * area_m2_total * niveles
viga_m3 = factor_viga_m3_por_m2 * area_m2_total * niveles
colviga_m3 = (col_m3 + viga_m3) * kf(depto, "col_viga")
colviga_m3 = aplicar_waste(colviga_m3, WASTE["col_viga"])

# -----------------------------
# Descomposición a materiales
# -----------------------------
def concreto_to_materiales(m3: float, receta: dict):
    cemento_bolsas = (receta["cemento_kg_por_m3"] * m3) / BOLSA_CEMENTO_KG
    arena_m3 = receta["arena_m3_por_m3"] * m3
    piedrin_m3 = receta["piedrin_m3_por_m3"] * m3
    agua_l = receta["agua_l_por_m3"] * m3
    acero_kg = receta["acero_kg_por_m3"] * m3
    return cemento_bolsas, arena_m3, piedrin_m3, agua_l, acero_kg

# Losa
losa_cem_bolsas, losa_arena_m3, losa_piedrin_m3, losa_agua_l, losa_acero_kg = concreto_to_materiales(losa_m3, CONCRETO)
# Contrapiso
cont_cem_bolsas, cont_arena_m3, cont_piedrin_m3, cont_agua_l, cont_acero_kg = concreto_to_materiales(contrapiso_m3, CONCRETO_CONTRAPISO)
# Cimientos
cim_cem_bolsas, cim_arena_m3, cim_piedrin_m3, cim_agua_l, cim_acero_kg = concreto_to_materiales(cimientos_m3, CONCRETO_CIMIENTOS)
# Columnas/Vigas
cv_cem_bolsas, cv_arena_m3, cv_piedrin_m3, cv_agua_l, cv_acero_kg = concreto_to_materiales(colviga_m3, CONCRETO_ESTRUCTURA)

# Muro de block
blocks_unid = MAMPOSTERIA["blocks_por_m2"] * muro_m2
mortero_cem_bolsas = (MAMPOSTERIA["mortero_cemento_kg_por_m2"] * muro_m2) / BOLSA_CEMENTO_KG
mortero_arena_m3 = MAMPOSTERIA["mortero_arena_m3_por_m2"] * muro_m2

# Totales
total_cemento_bolsas = sum([losa_cem_bolsas, cont_cem_bolsas, cim_cem_bolsas, cv_cem_bolsas, mortero_cem_bolsas])
total_arena_m3 = sum([losa_arena_m3, cont_arena_m3, cim_arena_m3, cv_arena_m3, mortero_arena_m3])
total_piedrin_m3 = sum([losa_piedrin_m3, cont_piedrin_m3, cim_piedrin_m3, cv_piedrin_m3])
total_agua_l = sum([losa_agua_l, cont_agua_l, cim_agua_l, cv_agua_l])
total_acero_kg = sum([losa_acero_kg, cont_acero_kg, cim_acero_kg, cv_acero_kg])

# -----------------------------
# Presentación
# -----------------------------
st.markdown("---")
st.subheader("Resultados estimados")

col_a, col_b, col_c = st.columns(3)
with col_a:
    st.metric("Cemento", f"{total_cemento_bolsas:,.1f} bolsas")
    st.metric("Blocks", f"{blocks_unid:,.0f} unidades")
with col_b:
    st.metric("Arena", f"{total_arena_m3:,.2f} m³")
    st.metric("Piedrín (Grava)", f"{total_piedrin_m3:,.2f} m³")
with col_c:
    st.metric("Acero", f"{total_acero_kg:,.0f} kg")
    st.metric("Agua", f"{total_agua_l:,.0f} L")

st.caption("Nota: 'Piedrín' y 'Grava' se usan como sinónimos en esta demo.")

with st.expander("Ver desglose por Actividad / Elemento Constructivo (Partida) y fórmulas"):
    st.markdown(f"""
**Suposiciones clave**
- Perímetro estimado: `sqrt(area_por_nivel) * 4` => {perimetro_m:,.2f} m (por nivel)
- Altura de muro: {altura_muro_m} m
- Losa: espesor {espesor_losa_m} m · niveles {niveles}
- Contrapiso: espesor {espesor_contrapiso_m} m
- Cimiento corrido: base {base_cimiento_m} m · altura {altura_cimiento_m} m

**Cantidades por Actividad / Elemento Constructivo (Partida)**
- Losa: {losa_m3:,.3f} m³
- Contrapiso: {contrapiso_m3:,.3f} m³
- Muros (block): {muro_m2:,.1f} m²
- Cimientos: {cimientos_m3:,.3f} m³
- Columnas+Vigas: {colviga_m3:,.3f} m³

**Materiales por Actividad / Elemento Constructivo (Partida)**
- Losa → cemento {losa_cem_bolsas:,.2f} bolsas · arena {losa_arena_m3:,.2f} m³ · piedrín {losa_piedrin_m3:,.2f} m³ · agua {losa_agua_l:,.0f} L · acero {losa_acero_kg:,.0f} kg
- Contrapiso → cemento {cont_cem_bolsas:,.2f} bolsas · arena {cont_arena_m3:,.2f} m³ · piedrín {cont_piedrin_m3:,.2f} m³ · agua {cont_agua_l:,.0f} L
- Cimientos → cemento {cim_cem_bolsas:,.2f} bolsas · arena {cim_arena_m3:,.2f} m³ · piedrín {cim_piedrin_m3:,.2f} m³ · agua {cim_agua_l:,.0f} L · acero {cim_acero_kg:,.0f} kg
- Columnas/Vigas → cemento {cv_cem_bolsas:,.2f} bolsas · arena {cv_arena_m3:,.2f} m³ · piedrín {cv_piedrin_m3:,.2f} m³ · agua {cv_agua_l:,.0f} L · acero {cv_acero_kg:,.0f} kg
- Muro block → blocks {blocks_unid:,.0f} unid · cemento mortero {mortero_cem_bolsas:,.2f} bolsas · arena mortero {mortero_arena_m3:,.2f} m³

**Ajustes por departamento (k-factor demo)**
- Guatemala: 1.00 · Quetzaltenango: 1.02–1.08 · Petén: 0.95–0.98
""")
# Crear tabla resumen
tabla = [
    {"Actividad / Elemento (Partida)": "Losa", "Unidad": "m³", "Cantidad": f"{losa_m3:,.2f}", 
     "Materiales principales": f"Cemento {losa_cem_bolsas:,.1f} bolsas, Arena {losa_arena_m3:,.2f} m³, Piedrín {losa_piedrin_m3:,.2f} m³"},
    {"Actividad / Elemento (Partida)": "Contrapiso", "Unidad": "m³", "Cantidad": f"{contrapiso_m3:,.2f}", 
     "Materiales principales": f"Cemento {cont_cem_bolsas:,.1f} bolsas, Arena {cont_arena_m3:,.2f} m³, Piedrín {cont_piedrin_m3:,.2f} m³"},
    {"Actividad / Elemento (Partida)": "Muros de block", "Unidad": "m²", "Cantidad": f"{muro_m2:,.1f}", 
     "Materiales principales": f"Blocks {blocks_unid:,.0f}, Mortero {mortero_cem_bolsas:,.1f} bolsas cemento + {mortero_arena_m3:,.2f} m³ arena"},
    {"Actividad / Elemento (Partida)": "Cimientos corridos", "Unidad": "m³", "Cantidad": f"{cimientos_m3:,.2f}", 
     "Materiales principales": f"Cemento {cim_cem_bolsas:,.1f} bolsas, Arena {cim_arena_m3:,.2f} m³, Piedrín {cim_piedrin_m3:,.2f} m³"},
    {"Actividad / Elemento (Partida)": "Columnas + Vigas", "Unidad": "m³", "Cantidad": f"{colviga_m3:,.2f}", 
     "Materiales principales": f"Cemento {cv_cem_bolsas:,.1f} bolsas, Arena {cv_arena_m3:,.2f} m³, Piedrín {cv_piedrin_m3:,.2f} m³"}
]

df_tabla = pd.DataFrame(tabla)
st.dataframe(df_tabla, use_container_width=True)
st.markdown("---")
st.caption("Demo sin conexión a bases externas. Ajusta coeficientes luego con tus datos reales.")
