import math
import io
import pandas as pd
import streamlit as st

# -------- Config --------
st.set_page_config(page_title="Calculadora de Materiales", page_icon="🏗️", layout="centered")
BOLSA_CEMENTO_KG = 42.5

# Coeficientes demo (ajustables más adelante)
CONCRETO = {"cemento_kg_por_m3": 320.0, "arena_m3_por_m3": 0.50, "piedrin_m3_por_m3": 0.70, "agua_l_por_m3": 180.0, "acero_kg_por_m3": 85.0}
CONCRETO_ESTRUCTURA = {"cemento_kg_por_m3": 340.0, "arena_m3_por_m3": 0.48, "piedrin_m3_por_m3": 0.72, "agua_l_por_m3": 185.0, "acero_kg_por_m3": 110.0}
CONCRETO_CIMIENTOS = {"cemento_kg_por_m3": 300.0, "arena_m3_por_m3": 0.50, "piedrin_m3_por_m3": 0.70, "agua_l_por_m3": 175.0, "acero_kg_por_m3": 40.0}
CONCRETO_CONTRAPISO = {"cemento_kg_por_m3": 280.0, "arena_m3_por_m3": 0.55, "piedrin_m3_por_m3": 0.65, "agua_l_por_m3": 170.0, "acero_kg_por_m3": 0.0}
MAMPOSTERIA = {"blocks_por_m2": 12.5, "mortero_cemento_kg_por_m2": 9.0, "mortero_arena_m3_por_m2": 0.018}

# Ajustes por departamento (demo)
K_FACTOR = {
    "Guatemala": {"losa": 1.00, "contrapiso": 1.00, "muro_block": 1.00, "cimientos": 1.00, "col_viga": 1.00},
    "Quetzaltenango": {"losa": 1.05, "contrapiso": 1.05, "muro_block": 1.08, "cimientos": 1.02, "col_viga": 1.06},
    "Petén": {"losa": 0.98, "contrapiso": 0.98, "muro_block": 0.95, "cimientos": 0.97, "col_viga": 0.96},
}

# Desperdicios (demo)
WASTE = {"losa": 0.05, "contrapiso": 0.05, "muro_block": 0.07, "cimientos": 0.05, "col_viga": 0.05}

# Parámetros base
ALTURA_MURO_M = 2.5
ESPESOR_LOSA_M = 0.12
ESPESOR_CONTRAPISO_M = 0.08
BASE_CIMIENTO_M = 0.50
ALTURA_CIMIENTO_M = 0.60
FACTOR_COL_M3_POR_M2 = 0.020
FACTOR_VIGA_M3_POR_M2 = 0.015

# -------- Helpers --------
def estimar_perimetro(area_m2: float) -> float:
    lado = math.sqrt(max(area_m2, 1e-6))
    return lado * 4.0

def aplicar_waste(x: float, waste: float) -> float:
    return x * (1.0 + waste)

def kf(depto: str, partida: str) -> float:
    return K_FACTOR.get(depto, {}).get(partida, 1.0)

def concreto_to_materiales(m3: float, receta: dict):
    cemento_bolsas = (receta["cemento_kg_por_m3"] * m3) / BOLSA_CEMENTO_KG
    arena_m3 = receta["arena_m3_por_m3"] * m3
    piedrin_m3 = receta["piedrin_m3_por_m3"] * m3
    agua_l = receta["agua_l_por_m3"] * m3
    acero_kg = receta["acero_kg_por_m3"] * m3
    return cemento_bolsas, arena_m3, piedrin_m3, agua_l, acero_kg

# -------- UI --------
st.markdown("### 🏗️ Calculadora de Materiales (Simple)")
st.caption("Ingresa 3 datos. Obtén cantidades estimadas en unidades comunes en Guatemala (bolsas, m³, kg, L).")

col1, col2, col3 = st.columns(3)
depto = col1.selectbox("Departamento", list(K_FACTOR.keys()), index=0)
niveles = col2.selectbox("Niveles", [1, 2, 3], index=1)
area_m2_total = col3.number_input("Área (m²)", min_value=20.0, max_value=1000.0, value=120.0, step=5.0)

# Aberturas (opcional)
st.markdown("#### Aberturas (opcional)")
colA, colB, colC = st.columns(3)
incluir_aberturas = colA.checkbox("Incluir puertas y ventanas", value=False)
if incluir_aberturas:
    n_habitaciones = colB.number_input("Habitaciones", min_value=0, max_value=20, value=3, step=1)
    n_banos = colC.number_input("Baños", min_value=0, max_value=20, value=2, step=1)
    c1, c2 = st.columns(2)
    with c1:
        metodo_aberturas = st.radio("Cálculo de ventanas", ["Por m² (factor)", "Por cuartos"], index=0, horizontal=True)
    with c2:
        factor_ventanas_por_m2 = st.number_input("Factor ventanas por m²", min_value=0.00, max_value=0.20, value=0.06, step=0.01, format="%.2f")
else:
    n_habitaciones = 0
    n_banos = 0
    metodo_aberturas = "Por m² (factor)"
    factor_ventanas_por_m2 = 0.06

calcular = st.button("Calcular ✅", use_container_width=True)
st.markdown("---")

if calcular:
    # Geometría base
    m2_por_nivel = area_m2_total / niveles
    perimetro_m = estimar_perimetro(m2_por_nivel)  # por nivel

    # Volúmenes/superficies base
    losa_m3 = aplicar_waste(m2_por_nivel * ESPESOR_LOSA_M * niveles * kf(depto, "losa"), WASTE["losa"])
    contrapiso_m3 = aplicar_waste(area_m2_total * ESPESOR_CONTRAPISO_M * kf(depto, "contrapiso"), WASTE["contrapiso"])
    muro_m2 = aplicar_waste(perimetro_m * ALTURA_MURO_M * niveles * kf(depto, "muro_block"), WASTE["muro_block"])
    cimientos_m3 = aplicar_waste(perimetro_m * BASE_CIMIENTO_M * ALTURA_CIMIENTO_M * kf(depto, "cimientos"), WASTE["cimientos"])
    col_m3 = FACTOR_COL_M3_POR_M2 * area_m2_total * niveles
    viga_m3 = FACTOR_VIGA_M3_POR_M2 * area_m2_total * niveles
    colviga_m3 = aplicar_waste((col_m3 + viga_m3) * kf(depto, "col_viga"), WASTE["col_viga"])

    # Materiales por concreto
    losa_cem, losa_ar, losa_pi, losa_agua, losa_ac = concreto_to_materiales(losa_m3, CONCRETO)
    cont_cem, cont_ar, cont_pi, cont_agua, cont_ac = concreto_to_materiales(contrapiso_m3, CONCRETO_CONTRAPISO)
    cim_cem, cim_ar, cim_pi, cim_agua, cim_ac = concreto_to_materiales(cimientos_m3, CONCRETO_CIMIENTOS)
    cv_cem, cv_ar, cv_pi, cv_agua, cv_ac = concreto_to_materiales(colviga_m3, CONCRETO_ESTRUCTURA)

    # Mampostería
    blocks_unid = MAMPOSTERIA["blocks_por_m2"] * muro_m2
    mortero_cem_bolsas = (MAMPOSTERIA["mortero_cemento_kg_por_m2"] * muro_m2) / BOLSA_CEMENTO_KG
    mortero_arena_m3 = MAMPOSTERIA["mortero_arena_m3_por_m2"] * muro_m2

    # Puertas y Ventanas (conteo simple)
    if incluir_aberturas:
        puertas_pzas = int(n_habitaciones + n_banos + 1)  # +1 entrada
        if metodo_aberturas == "Por m² (factor)":
            ventanas_pzas = int(round(area_m2_total * factor_ventanas_por_m2))
        else:
            ventanas_pzas = int(n_habitaciones + n_banos)  # aprox: una por cuarto/baño
    else:
        puertas_pzas = 0
        ventanas_pzas = 0

    # Totales
    total_cemento_bolsas = sum([losa_cem, cont_cem, cim_cem, cv_cem, mortero_cem_bolsas])
    total_arena_m3 = sum([losa_ar, cont_ar, cim_ar, cv_ar, mortero_arena_m3])
    total_piedrin_m3 = sum([losa_pi, cont_pi, cim_pi, cv_pi])
    total_agua_l = sum([losa_agua, cont_agua, cim_agua, cv_agua])
    total_acero_kg = sum([losa_ac, cont_ac, cim_ac, cv_ac])

    # Métricas grandes
    st.markdown("#### Resultado")
    mcol1, mcol2, mcol3 = st.columns(3)
    with mcol1:
        st.metric("Cemento", f"{total_cemento_bolsas:,.1f} bolsas")
        st.metric("Blocks", f"{blocks_unid:,.0f} unidades")
    with mcol2:
        st.metric("Arena", f"{total_arena_m3:,.2f} m³")
        st.metric("Piedrín (Grava)", f"{total_piedrin_m3:,.2f} m³")
    with mcol3:
        st.metric("Acero", f"{total_acero_kg:,.0f} kg")
        st.metric("Agua", f"{total_agua_l:,.0f} L")

    if incluir_aberturas and (puertas_pzas or ventanas_pzas):
        st.markdown(f"**Aberturas estimadas:** Puertas: {puertas_pzas} pzas · Ventanas: {ventanas_pzas} pzas")

    st.caption("Valores de demostración. 'Piedrín' y 'Grava' se usan como sinónimos.")

    # Desglose compacto + descarga CSV
    with st.expander("Ver desglose por Actividad / Elemento Constructivo (Partida)"):
        tabla = [
            {"Actividad / Elemento (Partida)": "Losa", "Unidad": "m³", "Cantidad": f"{losa_m3:,.2f}",
             "Materiales principales": f"Cemento {losa_cem:,.1f} bolsas, Arena {losa_ar:,.2f} m³, Piedrín {losa_pi:,.2f} m³, Acero {losa_ac:,.0f} kg"},
            {"Actividad / Elemento (Partida)": "Contrapiso", "Unidad": "m³", "Cantidad": f"{contrapiso_m3:,.2f}",
             "Materiales principales": f"Cemento {cont_cem:,.1f} bolsas, Arena {cont_ar:,.2f} m³, Piedrín {cont_pi:,.2f} m³"},
            {"Actividad / Elemento (Partida)": "Muros de block", "Unidad": "m²", "Cantidad": f"{muro_m2:,.1f}",
             "Materiales principales": f"Blocks {blocks_unid:,.0f} unid, Mortero {mortero_cem_bolsas:,.1f} bolsas cemento + {mortero_arena_m3:,.2f} m³ arena"},
            {"Actividad / Elemento (Partida)": "Cimientos corridos", "Unidad": "m³", "Cantidad": f"{cimientos_m3:,.2f}",
             "Materiales principales": f"Cemento {cim_cem:,.1f} bolsas, Arena {cim_ar:,.2f} m³, Piedrín {cim_pi:,.2f} m³, Acero {cim_ac:,.0f} kg"},
            {"Actividad / Elemento (Partida)": "Columnas + Vigas", "Unidad": "m³", "Cantidad": f"{colviga_m3:,.2f}",
             "Materiales principales": f"Cemento {cv_cem:,.1f} bolsas, Arena {cv_ar:,.2f} m³, Piedrín {cv_pi:,.2f} m³, Acero {cv_ac:,.0f} kg"}
        ]

        if incluir_aberturas:
            tabla.append({"Actividad / Elemento (Partida)": "Puertas (conteo)", "Unidad": "pza", "Cantidad": f"{puertas_pzas:d}", "Materiales principales": "Carpintería/metal según catálogo (no desglosado en demo)"})
            tabla.append({"Actividad / Elemento (Partida)": "Ventanas (conteo)", "Unidad": "pza", "Cantidad": f"{ventanas_pzas:d}", "Materiales principales": "Vidrio/Aluminio según catálogo (no desglosado en demo)"})

        df_tabla = pd.DataFrame(tabla)
        st.dataframe(df_tabla, use_container_width=True)

        csv_buffer = io.StringIO()
        df_tabla.to_csv(csv_buffer, index=False)
        st.download_button("Descargar desglose (CSV)", data=csv_buffer.getvalue(), file_name="desglose_materiales_demo_simple.csv", mime="text/csv", use_container_width=True)

st.markdown(
    """
    <style>
    div.stButton > button:first-child {
        background-color: #1E88E5;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)
st.markdown("---")
st.caption("Prototipo mínimo. Luego conectamos tus coeficientes reales y precios por departamento.")
