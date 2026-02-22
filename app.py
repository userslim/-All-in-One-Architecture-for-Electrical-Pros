import streamlit as st
import math
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- CLASS CONTINUATION ---
class SGProEngine:
    def __init__(self):
        # [All your previous initialization code here...]
        # ... (Assuming the previous code is present)
        
        # Finishing the line that was cut off:
        self.energy_optimization_algorithms = {
            "load_shedding": "Shed non-essential loads during peak demand",
            "peak_shaving": "Use generator/battery during peak tariff periods",
            "demand_response": "Reduce load when grid requests",
            "load_balancing": "Balance loads across phases",
            "power_factor_correction": "Maintain power factor above 0.90 to avoid penalties"
        }

    # --- CALCULATION METHODS ---

    def calculate_lighting(self, room_type, length, width):
        """Calculates number of fittings based on your lighting_standards database."""
        area = length * width
        std = self.lighting_standards.get(room_type)
        
        # Using the Lumen Method simplified for design estimate
        total_lumens_needed = area * std['recommended_lux'] / (0.6 * 0.8) # 0.6 UF, 0.8 LLF
        num_fittings = math.ceil(total_lumens_needed / std['lumens_per_fitting'])
        total_load = num_fittings * std['watt_per_fitting']
        
        return {
            "fittings": num_fittings,
            "load_w": total_load,
            "details": std
        }

    def calculate_voltage_drop(self, load_amps, length_m, cable_size, pf=0.85, system_v=400):
        """Calculates Voltage Drop using the R and X values from your impedance database."""
        imp = self.cable_impedance.get(cable_size)
        phi = math.acos(pf)
        
        # VD = sqrt(3) * I * L * (Rcosphi + Xsinphi) / 1000
        r_comp = imp['r'] * math.cos(phi)
        x_comp = imp['x'] * math.sin(phi)
        vd = (math.sqrt(3) * load_amps * length_m * (r_comp + x_comp)) / 1000
        vd_percentage = (vd / system_v) * 100
        
        return round(vd, 2), round(vd_percentage, 2)

# --- STREAMLIT UI ---

st.set_page_config(page_title="SG Electrical Pro Engine", layout="wide")
engine = SGProEngine()

st.title("⚡ SG Pro: All-in-one Electrical Architecture")
menu = st.sidebar.selectbox("Navigation", ["Lighting Designer", "Cable & VD Calculator", "Maintenance Scheduler", "BIM/IoT Dashboard"])

# 1. LIGHTING DESIGNER PAGE
if menu == "Lighting Designer":
    st.header("💡 Automated Lighting Design (SS 531)")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        room = st.selectbox("Room Category", list(engine.lighting_standards.keys()))
        l = st.number_input("Room Length (m)", value=10.0)
        w = st.number_input("Room Width (m)", value=10.0)
        result = engine.calculate_lighting(room, l, w)

    with col2:
        st.subheader("Design Result")
        c1, c2, c3 = st.columns(3)
        c1.metric("Fittings Required", f"{result['fittings']} pcs")
        c2.metric("Total Load", f"{result['load_w']} W")
        c3.metric("Lux Level", f"{result['details']['recommended_lux']} lx")
        
        st.info(f"**Recommended Fitting:** {result['details']['fitting_type']} ({result['details']['color_temp']})")

# 2. CABLE & VD CALCULATOR PAGE
elif menu == "Cable & VD Calculator":
    st.header("🔌 Cable Sizing & Voltage Drop")
    
    col1, col2 = st.columns(2)
    with col1:
        load = st.number_input("Design Current (Amps)", value=100.0)
        dist = st.number_input("Route Length (m)", value=50.0)
        size = st.selectbox("Cable Size (sqmm)", list(engine.cable_impedance.keys()))
        pf_val = st.slider("Power Factor", 0.7, 1.0, 0.85)

    vd_v, vd_p = engine.calculate_voltage_drop(load, dist, size, pf_val)
    
    with col2:
        st.subheader("Analysis")
        st.metric("Voltage Drop (V)", f"{vd_v} V")
        st.metric("Voltage Drop (%)", f"{vd_p} %")
        
        if vd_p > 4.0:
            st.error("⚠️ Fails SS 638: Voltage drop exceeds 4% for services.")
        else:
            st.success("✅ Complies with SS 638 standards.")

# 3. MAINTENANCE SCHEDULER
elif menu == "Maintenance Scheduler":
    st.header("📅 Predictive Maintenance Schedule")
    freq = st.radio("View Frequency", ["daily", "weekly", "monthly", "annually"])
    
    tasks = engine.maintenance_templates[freq]
    df = pd.DataFrame(tasks)
    st.table(df)
    
    # Visualizing Lifetime
    st.subheader("Asset Health (Digital Twin)")
    fig = go.Figure(go.Bar(
        x=list(engine.equipment_lifetime.keys()),
        y=list(engine.equipment_lifetime.values()),
        marker_color='teal'
    ))
    fig.update_layout(title="Standard Asset Life Expectancy (Hours/Years)")
    st.plotly_chart(fig)
