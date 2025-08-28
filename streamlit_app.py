import streamlit as st
import pandas as pd
import math
import io

# -------- Config --------
st.set_page_config(page_title="Calculadora de Materiales Comparativa", page_icon="🏗️", layout="wide")

BOLSA_CEMENTO_KG = 42.5

# Datos de ejemplo
CONCRETO = {"cemento_kg_por_m3": 320, "arena_m3_por_m3": 0.50, "piedrin_m3_por_m3": 0.70, "agua_l_por_m3": 180, "acero_kg_por_m3": 85}
CONCRETO_ESTRUCTURA = {"cemento_kg_por_m3": 340, "arena_m3_por_m3": 0.48, "piedrin_m3_por_m3": 0.72, "agua_l_por_m3": 185, "acero_kg_por_m3": 110}
CONCRETO_CIMIENTOS = {"cemento_kg_por_m3": 300, "arena_m3_por_m3": 0.50, "piedrin_m3_por_m3": 0.70, "agua_l_por_m3": 175, "acero_kg_por_m3": 40}
CONCRETO_CONTRAPISO = {"cemento_kg_por_m3": 280, "arena_m3_por_m3": 0.55, "piedrin_m3_por_m3": 0.65, "agua_l_por_m3": 170, "acero_kg_por_m3": 0}
MAMPOSTERIA = {"blocks_por_m2": 12.5, "mortero_cemento_kg_por_m2": 9.0, "mortero_arena_m3_por_m2": 0.018}

K_FACTOR = {
    "Guatemala": {"losa": 1.00, "contrapiso": 1.00, "muro_block": 1.00, "cimientos": 1.00, "col_viga": 1.00},
    "Quetzaltenango": {"losa": 1.05, "contrapiso": 1.05, "muro_block": 1.08, "cimientos": 1.02, "col_viga": 1.06},
    "Petén": {"losa": 0.98, "contrapiso": 0.98, "muro_block": 0.95, "cimientos": 0.97, "col_viga": 0.96}
}
WASTE = {"losa": 0.05, "contrapiso": 0.05, "muro_block": 0.07, "cimientos": 0.05, "col_viga": 0.05}

# Parámetros constructivos base
ESPESOR_LOSA_M = 0.12
ESPESOR_CONTRAPISO_M = 0.08
ALTURA_MURO_M = 2.5
BASE_CIMIENTO_M = 0.50
ALTURA_CIMIENTO_M = 0.60
FACTOR_COL_M3_POR_M2 = 0.020
FACTOR_VIGA_M3_POR_M2 = 0.015

TIPOS_CONSTRUCCION = [
    "Casa completa", "Cuartos", "Cercas/Muros", "Locales Comerciales", "Techos", "Paredes", "Piso",
    "Ventanas", "Puertas", "Sanitario", "Terrazas", "Depósito de Agua", "Otro Nivel"
]

# ------------------ Funciones ------------------
def estimar_perimetro(area_m2):
    lado = math.sqrt(max(area_m2, 1e-6))
    return lado * 4

def aplicar_waste(valor, waste):
    return valor * (1 + waste)

def kf(depto, partida):
    return K_FACTOR.get(depto, {}).get(partida, 1.0)

def concreto_to_materiales(m3, receta):
    return {
        "cemento_bolsas": (receta["cemento_kg_por_m3"] * m3) / BOLSA_CEMENTO_KG,
        "arena_m3": receta["arena_m3_por_m3"] * m3,
        "piedrin_m3": receta["piedrin_m3_por_m3"] * m3,
        "agua_l": receta["agua_l_por_m3"] * m3,
        "acero_kg": receta["acero_kg_por_m3"] * m3,
    }

def calcular_materiales(config):
    area_m2 = config["area"]
    niveles = config["niveles"]
    depto = config["depto"]
    cuartos = config["cuartos"]
    banos = config["banos"]

    m2_por_nivel = area_m2 / niveles
    perimetro_m = estimar_perimetro(m2_por_nivel)

    losa_m3 = aplicar_waste(m2_por_nivel * ESPESOR_LOSA_M * niveles * kf(depto, "losa"), WASTE["losa"])
    contrapiso_m3 = aplicar_waste(area_m2 * ESPESOR_CONTRAPISO_M * kf(depto, "contrapiso"), WASTE["contrapiso"])
    muro_m2 = aplicar_waste(perimetro_m * ALTURA_MURO_M * niveles * kf(depto, "muro_block"), WASTE["muro_block"])
    cimientos_m3 = aplicar_waste(perimetro_m * BASE_CIMIENTO_M * ALTURA_CIMIENTO_M * kf(depto, "cimientos"), WASTE["cimientos"])
    colviga_m3 = aplicar_waste((FACTOR_COL_M3_POR_M2 + FACTOR_VIGA_M3_POR_M2) * area_m2 * niveles * kf(depto, "col_viga"), WASTE["col_viga"])

    materiales = {"cemento_bolsas": 0, "arena_m3": 0, "piedrin_m3": 0, "agua_l": 0, "acero_kg": 0, "blocks": 0}
    for vol, receta in zip(
        [losa_m3, contrapiso_m3, cimientos_m3, colviga_m3],
        [CONCRETO, CONCRETO_CONTRAPISO, CONCRETO_CIMIENTOS, CONCRETO_ESTRUCTURA]
    ):
        mat = concreto_to_materiales(vol, receta)
        for k in materiales:
            if k in mat:
                materiales[k] += mat[k]

    bloques = MAMPOSTERIA["blocks_por_m2"] * muro_m2
    mortero_cem = MAMPOSTERIA["mortero_cemento_kg_por_m2"] * muro_m2 / BOLSA_CEMENTO_KG
    mortero_arena = MAMPOSTERIA["mortero_arena_m3_por_m2"] * muro_m2

    materiales["cemento_bolsas"] += mortero_cem
    materiales["arena_m3"] += mortero_arena
    materiales["blocks"] = bloques

    puertas = cuartos + banos + 1
    ventanas = cuartos + banos

    return {
        "materiales": materiales,
        "puertas": puertas,
        "ventanas": ventanas,
        "resumen": f"{area_m2} m² - {niveles} niveles - {cuartos} cuartos - {banos} baños"
    }

# ------------------ Interfaz ------------------
# -------- Título --------
st.markdown("# 🏗️ Calculadora de Materiales Comparativa")
st.caption("Estima materiales para construcción en distintas ubicaciones, años y configuraciones.")

n_comparar = st.slider("¿Cuántas configuraciones quieres comparar?", 1, 3, 2, 1)

configs = []
for i in range(n_comparar):
    with st.expander(f"🏠 Construcción #{i+1}", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            anio = st.selectbox(f"Año", [2023, 2024, 2025], key=f"anio_{i}")
        with col2:
            depto = st.selectbox(f"Departamento", list(K_FACTOR.keys()), key=f"depto_{i}")
        with col3:
            tipo = st.selectbox(f"Tipo de Construcción", TIPOS_CONSTRUCCION, key=f"tipo_{i}")

        col4, col5, col6 = st.columns(3)
        with col4:
            niveles = st.number_input("Niveles", 1, 5, 1, key=f"niveles_{i}")
        with col5:
            area = st.number_input("Área (m²)", 20, 1000, 120, step=10, key=f"area_{i}")
        with col6:
            cuartos = st.number_input("Habitaciones", 0, 20, 3, key=f"cuartos_{i}")
            banos = st.number_input("Baños", 0, 10, 2, key=f"banos_{i}")

        configs.append({
            "anio": anio, "depto": depto, "tipo": tipo,
            "niveles": niveles, "area": area,
            "cuartos": cuartos, "banos": banos
        })

st.markdown("---")
if st.button("Calcular ✅", use_container_width=True):
    resultados = []
    for i, config in enumerate(configs):
        calc = calcular_materiales(config)
        mat = calc["materiales"]
        resultados.append({
            "Casa": f"#{i+1}",
            "Año": config["anio"],
            "Departamento": config["depto"],
            "Tipo": config["tipo"],
            "Área (m²)": config["area"],
            "Niveles": config["niveles"],
            "Cuartos": config["cuartos"],
            "Baños": config["banos"],
            "Cemento (bolsas)": round(mat["cemento_bolsas"], 1),
            "Arena (m³)": round(mat["arena_m3"], 2),
            "Piedrín (m³)": round(mat["piedrin_m3"], 2),
            "Blocks (unid)": round(mat["blocks"]),
            "Acero (kg)": round(mat["acero_kg"]),
            "Agua (L)": round(mat["agua_l"]),
            "Puertas": calc["puertas"],
            "Ventanas": calc["ventanas"]
        })

    df = pd.DataFrame(resultados)
    st.markdown(f"### 📊 {'Comparativa' if n_comparar > 1 else 'Resultados'}")
    st.dataframe(df, use_container_width=True)

    csv = io.StringIO()
    df.to_csv(csv, index=False)
    st.download_button("📥 Descargar comparación CSV", csv.getvalue(), "comparacion_construcciones.csv", "text/csv")

