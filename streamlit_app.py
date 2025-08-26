import math
import io
import pandas as pd
import streamlit as st

# -----------------------------
# Configuración general
# -----------------------------
st.set_page_config(page_title="Calculadora de Materiales (Demo UX)", page_icon="🏗️", layout="centered")

# -----------------------------
# Constantes y coeficientes (demo)
# -----------------------------
BOLSA_CEMENTO_KG = 42.5

CONCRETO = {"cemento_kg_por_m3": 320.0, "arena_m3_por_m3": 0.50, "piedrin_m3_por_m3": 0.70, "agua_l_por_m3": 180.0, "acero_kg_por_m3": 85.0}
CONCRETO_ESTRUCTURA = {"cemento_kg_por_m3": 340.0, "arena_m3_por_m3": 0.48, "piedrin_m3_por_m3": 0.72, "agua_l_por_m3": 185.0, "acero_kg_por_m3": 110.0}
CONCRETO_CIMIENTOS = {"cemento_kg_por_m3": 300.0, "arena_m3_por_m3": 0.50, "piedrin_m3_por_m3": 0.70, "agua_l_por_m3": 175.0, "acero_kg_por_m3": 40.0}
CONCRETO_CONTRAPISO = {"cemento_kg_por_m3": 280.0, "arena_m3_por_m3": 0.55, "piedrin_m3_por_m3": 0.65, "agua_l_por_m3": 170.0, "acero_kg_por_m3": 0.0}

MAMPOSTERIA = {"blocks_por_m2": 12.5, "mortero_cemento_kg_por_m2": 9.0, "mortero_arena_m3_por_m2": 0.018}

K_FACTOR = {
    "Guatemala": {"losa": 1.00, "contrapiso": 1.00, "muro_block": 1.00, "cimientos": 1.00, "col_viga": 1.00},
    "Quetzaltenango": {"losa": 1.05, "contrapiso": 1.05, "muro_block": 1.08, "cimientos": 1.02, "col_viga": 1.06},
    "Petén": {"losa": 0.98, "contrapiso": 0.98, "muro_block": 0.95, "cimientos": 0.97, "col_viga": 0.96},
}

WASTE = {"losa": 0.05, "contrapiso": 0.05, "muro_block": 0.07, "cimientos": 0.05, "col_viga": 0.05}

ALTURA_MURO_M = 2.5
ESPESOR_LOSA_M = 0.12
ESPESOR_CONTRAPISO_M = 0.08
BASE_CIMIENTO_M = 0.50
ALTURA_CIMIENTO_M = 0.60

FACTOR_COL_M3_POR_M2 = 0.020
FACTOR_VIGA_M3_POR_M2 = 0.015

# -----------------------------
# Funciones
# -----------------------------
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

# -----------------------------
# UI — Diseño simple
# -----------------------------
st.markdown("## 🏗️ Calculadora de Materiales (Demo)")
st.caption("Súper simple: elige **Departamento**, **Niveles** y **Área (m²)**. Obtendrás cantidades estimadas de cemento, arena, piedrín (grava), blocks, acero y agua.")

# Tabs: Básico (para cualquiera) y Avanzado (opcional)
tab_basic, tab_adv = st.tabs(["Modo Básico", "Modo Avanzado"])

with tab_basic:
    # Chips rápidas: presets de área
    st.markdown("**Tamaños rápidos**:")
    cols = st.columns(6)
    presets = [60, 80, 100, 120, 150, 180]
    for i, p in enumerate(presets):
        if cols[i].button(f"{p} m²"):
            st.session_state["area_quick"] = float(p)

    # Entrada principal
    col1, col2, col3 = st.columns(3)
    depto = col1.selectbox("Departamento", list(K_FACTOR.keys()), index=0, help="Ajusta proporciones locales de materiales.")
    niveles = col2.selectbox("Niveles", [1, 2, 3], index=1, help="Pisos de la casa.")
    default_area = st.session_state.get("area_quick", 120.0)
    area_m2_total = col3.number_input("Área construida total (m²)", min_value=20.0, max_value=1000.0, value=float(default_area), step=5.0)

    st.markdown("---")
    calc = st.button("Calcular ✅", type="primary", use_container_width=True)

    if calc:
        # Geometría base
        m2_por_nivel = area_m2_total / niveles
        perimetro_m = estimar_perimetro(m2_por_nivel)  # por nivel

        # Losa (m3)
        losa_m3 = aplicar_waste(m2_por_nivel * ESPESOR_LOSA_M * niveles * kf(depto, "losa"), WASTE["losa"])

        # Contrapiso (m3)
        contrapiso_m3 = aplicar_waste(area_m2_total * ESPESOR_CONTRAPISO_M * kf(depto, "contrapiso"), WASTE["contrapiso"])

        # Muros (m2)
        muro_m2 = aplicar_waste(perimetro_m * ALTURA_MURO_M * niveles * kf(depto, "muro_block"), WASTE["muro_block"])

        # Cimientos (m3)
        cimientos_m3 = aplicar_waste(perimetro_m * BASE_CIMIENTO_M * ALTURA_CIMIENTO_M * kf(depto, "cimientos"), WASTE["cimientos"])

        # Col + Viga (m3)
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

        # Totales
        total_cemento_bolsas = sum([losa_cem, cont_cem, cim_cem, cv_cem, mortero_cem_bolsas])
        total_arena_m3 = sum([losa_ar, cont_ar, cim_ar, cv_ar, mortero_arena_m3])
        total_piedrin_m3 = sum([losa_pi, cont_pi, cim_pi, cv_pi])
        total_agua_l = sum([losa_agua, cont_agua, cim_agua, cv_agua])
        total_acero_kg = sum([losa_ac, cont_ac, cim_ac, cv_ac])

        # Métricas grandes
        st.markdown("### Resultado rápido")
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

        st.caption("Nota: 'Piedrín' y 'Grava' se usan como sinónimos. Valores de demostración sujetos a calibración.")

        # Expander con tabla y fórmulas
        with st.expander("Ver desglose por Actividad / Elemento Constructivo (Partida) y fórmulas"):
            st.markdown("**Cantidades por Actividad / Elemento Constructivo (Partida)**")

            # Tabla estilo planilla
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
                 "Materiales principales": f"Cemento {cv_cem:,.1f} bolsas, Arena {cv_ar:,.2f} m³, Piedrín {cv_pi:,.2f} m³, Acero {cv_ac:,.0f} kg"},
            ]
            df_tabla = pd.DataFrame(tabla)
            st.dataframe(df_tabla, use_container_width=True)

            st.markdown("**Fórmulas clave (demo)**")
            st.code(
                f"""
Perímetro por nivel ≈ sqrt(area_por_nivel) * 4 = {perimetro_m:,.2f} m
Losa (m³) = (Área por nivel * espesor) * niveles
Contrapiso (m³) = Área total * espesor_contrapiso
Muros (m²) = Perímetro * altura_muro * niveles
Cimientos (m³) = Perímetro * base_cimiento * altura_cimiento
Columnas + Vigas (m³) = (factor_col + factor_viga) * área_total * niveles
Aplicar k-factor por Departamento y % de desperdicio por actividad
""", language="text")

        # Descarga CSV del desglose
        st.markdown("### Exportar")
        csv_buffer = io.StringIO()
        df_tabla.to_csv(csv_buffer, index=False)
        st.download_button("Descargar desglose (CSV)", data=csv_buffer.getvalue(), file_name="desglose_materiales_demo.csv", mime="text/csv", use_container_width=True)

with tab_adv:
    st.markdown("### Parámetros (opcional)")
    with st.form("adv_form"):
        altura_muro_m = st.number_input("Altura de muro (m)", min_value=2.2, max_value=3.2, value=ALTURA_MURO_M, step=0.1)
        espesor_losa_m = st.number_input("Espesor losa (m)", min_value=0.08, max_value=0.20, value=ESPESOR_LOSA_M, step=0.01)
        espesor_contrapiso_m = st.number_input("Espesor contrapiso (m)", min_value=0.05, max_value=0.12, value=ESPESOR_CONTRAPISO_M, step=0.005)
        base_cimiento_m = st.number_input("Base cimiento corrido (m)", min_value=0.30, max_value=0.80, value=BASE_CIMIENTO_M, step=0.05)
        altura_cimiento_m = st.number_input("Altura cimiento corrido (m)", min_value=0.40, max_value=0.80, value=ALTURA_CIMIENTO_M, step=0.05)
        factor_col_m3_por_m2 = st.number_input("Factor columnas (m³ por m²)", min_value=0.005, max_value=0.05, value=FACTOR_COL_M3_POR_M2, step=0.001, format="%.3f")
        factor_viga_m3_por_m2 = st.number_input("Factor vigas (m³ por m²)", min_value=0.005, max_value=0.05, value=FACTOR_VIGA_M3_POR_M2, step=0.001, format="%.3f")

        st.caption("Estos parámetros se aplicarán en la próxima corrida del Modo Básico.")
        submitted = st.form_submit_button("Guardar cambios")

st.markdown("---")
st.caption("Prototipo UX — no usa Excel aún. Cuando lo valides, conectamos tus coeficientes reales y precios por departamento.")
