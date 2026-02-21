import streamlit as st
import pandas as pd
import math

# --- APP CONFIG ---
st.set_page_config(page_title="Pro Electrical Suite & Estimator", layout="wide")
st.title("⚡ All-in-One Electrical Design & Costing Suite")

# --- BUDGETARY UNIT COSTS (Estimated - User can adjust) ---
st.sidebar.header("💰 Budgetary Unit Costs")
cost_per_kva_gen = st.sidebar.number_input("Generator ($/kVA)", value=250)
cost_per_amp_mccb = st.sidebar.number_input("Main Breaker ($/Amp)", value=5.0)
cost_per_sqmm_m = st.sidebar.number_input("Cable ($/mm²/meter)", value=0.15)
cost_per_earth_pit = st.sidebar.number_input("Earth Pit ($/unit)", value=450)
cost_per_mcb = st.sidebar.number_input("10A MCB ($/unit)", value=15.0)

# --- DATA DICTIONARIES ---
CABLE_SPECS = {1.5: (23, 25.0), 2.5: (31, 15.0), 4: (42, 9.5), 6: (54, 6.4), 10: (75, 3.8), 16: (100, 2.4), 25: (133, 1.5), 35: (164, 1.1), 50: (198, 0.8), 70: (253, 0.57)}
STANDARD_GENS = [20, 30, 45, 60, 80, 100, 125, 150, 200, 250, 300, 400, 500, 750, 1000]

# --- TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["🏗️ Cable & Breaker", "🔋 Generator & Essential", "🌍 Earthing", "💡 Lighting"])

# --- TAB 1: CABLE & BREAKER ---
with tab1:
    st.header("Cable & Breaker Design")
    load_kva = st.number_input("Design Load (kVA)", value=100.0)
    voltage = st.selectbox("Voltage (V)", [415, 400, 230])
    length = st.number_input("Cable Length (m)", value=50)
    
    ib = (load_kva * 1000) / (1.732 * voltage)
    in_rating = ib * 1.25
    
    # Selection Logic
    final_sqmm = 1.5
    for sqmm, (cap, mv) in CABLE_SPECS.items():
        if cap > in_rating:
            if ((mv * ib * length) / 1000 / voltage) * 100 <= 3.0:
                final_sqmm = sqmm
                break

    breaker_cost = in_rating * cost_per_amp_mccb
    cable_cost = final_sqmm * length * cost_per_sqmm_m
    st.success(f"Cable: {final_sqmm}mm² | Breaker: {round(in_rating)}A")

# --- TAB 2: GENERATOR & ESSENTIAL SERVICES ---
with tab2:
    st.header("Emergency Power & Life Safety")
    colA, colB = st.columns(2)
    with colA:
        lift = st.checkbox("Lift Homing (Essential)", value=True)
        elights = st.checkbox("Emergency Lighting (Essential)", value=True)
    with colB:
        firepump = st.checkbox("Fire Pump (Essential)", value=False)
    
    essential_kva = (15.0 if lift else 0) + (5.0 if elights else 0) + (45.0 if firepump else 0)
    peak_kva = essential_kva * 1.5 # Avg Inrush
    recommended_gen = next((x for x in STANDARD_GENS if x >= peak_kva), 1000)
    
    gen_cost = recommended_gen * cost_per_kva_gen
    st.metric("Recommended Generator", f"{recommended_gen} kVA", f"${gen_cost:,.0f}")



# --- TAB 3: EARTHING ---
with tab3:
    st.header("Earthing Design")
    pits = st.slider("Number of Earth Pits", 1, 10, 2)
    earth_cost = pits * cost_per_earth_pit
    st.metric("Earthing Total", f"{pits} Pits", f"${earth_cost:,.0f}")

# --- TAB 4: LIGHTING ---
with tab4:
    st.header("Final Circuit Distribution")
    total_watts = st.number_input("Total Light Wattage", value=3000)
    num_circuits = math.ceil(total_watts / 1000)
    lighting_cost = num_circuits * cost_per_mcb
    st.metric("Lighting Circuits", f"{num_circuits} MCBs", f"${lighting_cost:,.0f}")

# --- SUMMARY & REPORT ---
st.divider()
total_project_cost = breaker_cost + cable_cost + gen_cost + earth_cost + lighting_cost

col_sum1, col_sum2 = st.columns([2,1])
with col_sum1:
    st.subheader("📋 Integrated Project Report")
    report_text = f"""
PROJECT SUMMARY REPORT
-----------------------------------
1. MAIN POWER:
   - Breaker: {round(in_rating)}A MCCB
   - Cable: {final_sqmm}mm² x {length}m
   - Estimated Sub-Total: ${breaker_cost + cable_cost:,.2f}

2. EMERGENCY SYSTEM:
   - Essential Load: {essential_kva} kVA
   - Generator: {recommended_gen} kVA Standby
   - Estimated Sub-Total: ${gen_cost:,.2f}

3. INFRASTRUCTURE:
   - Earth Pits: {pits} units
   - Lighting Circuits: {num_circuits} nos
   - Estimated Sub-Total: ${earth_cost + lighting_cost:,.2f}

TOTAL ESTIMATED BUDGET: ${total_project_cost:,.2f}
-----------------------------------
    """
    st.text_area("Report Preview", report_text, height=300)

with col_sum2:
    st.subheader("Budget Allocation")
    # Simple chart logic
    chart_data = pd.DataFrame({
        'Category': ['Power', 'Gen-Set', 'Infra'],
        'Cost': [breaker_cost + cable_cost, gen_cost, earth_cost + lighting_cost]
    })
    st.bar_chart(chart_data.set_index('Category'))



st.download_button("📥 Download Full Report", report_text, "Electrical_Project_Report.txt")