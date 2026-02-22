import streamlit as st
import math
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

class SGProEngine:
    def __init__(self):
        # Standard Frames & Trips
        self.standard_frames = [63, 100, 125, 160, 250, 400, 630, 800, 1000, 1250, 1600, 2000, 2500, 3200, 4000]
        self.standard_trips = [6, 10, 16, 20, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 320, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3200, 4000]
        
        # Cable Iz (Current Capacity) - Table 4E4A
        self.cable_db = {
            1.5: 25, 2.5: 33, 4: 43, 6: 56, 10: 77, 16: 102, 25: 135, 35: 166, 
            50: 201, 70: 255, 95: 309, 120: 358, 150: 410, 185: 469, 240: 551, 300: 627,
            400: 750, 500: 860, 630: 980
        }
        
        # Cable Impedance (R & X)
        self.cable_impedance = {
            1.5: {"r": 14.8, "x": 0.145}, 2.5: {"r": 8.91, "x": 0.135},
            4: {"r": 5.57, "x": 0.125}, 6: {"r": 3.71, "x": 0.120},
            10: {"r": 2.24, "x": 0.115}, 16: {"r": 1.41, "x": 0.110},
            25: {"r": 0.889, "x": 0.105}, 35: {"r": 0.641, "x": 0.100},
            50: {"r": 0.473, "x": 0.100}, 70: {"r": 0.328, "x": 0.095},
            95: {"r": 0.236, "x": 0.095}, 120: {"r": 0.188, "x": 0.090},
            150: {"r": 0.153, "x": 0.090}, 185: {"r": 0.124, "x": 0.090},
            240: {"r": 0.0991, "x": 0.085}, 300: {"r": 0.0795, "x": 0.085}
        }
        
        # Lighting Standards (The database that was causing the error)
        self.lighting_standards = {
            "Office (Open Plan)": {"recommended_lux": 400, "lumens_per_fitting": 3600, "watt_per_fitting": 36, "fitting_type": "LED Panel"},
            "Meeting Room": {"recommended_lux": 500, "lumens_per_fitting": 3500, "watt_per_fitting": 35, "fitting_type": "Dimmable LED"},
            "Car Park": {"recommended_lux": 75, "lumens_per_fitting": 4000, "watt_per_fitting": 40, "fitting_type": "LED Batten"},
            "Kitchen (Commercial)": {"recommended_lux": 500, "lumens_per_fitting": 4000, "watt_per_fitting": 40, "fitting_type": "IP65 Batten"}
        }

        # Maintenance Templates
        self.equipment_lifetime = {"LED Lighting": 50000, "MCB/MCCB": 20, "Cables": 30, "Generator": 20}
        self.maintenance_templates = {
            "daily": [{"task": "Gen-set Check", "duration": 15}],
            "monthly": [{"task": "Thermal Scan", "duration": 90}]
        }

    # --- CALCULATION METHODS ---
    def calculate_lighting(self, room_type, length, width):
        area = length * width
        std = self.lighting_standards.get(room_type)
        total_lumens = area * std['recommended_lux'] / (0.48) # 0.6 UF * 0.8 LLF
        num_fittings = math.ceil(total_lumens / std['lumens_per_fitting'])
        return {"fittings": num_fittings, "load_w": num_fittings * std['watt_per_fitting'], "details": std}

    def calculate_voltage_drop(self, load_amps, length_m, cable_size):
        imp = self.cable_impedance.get(cable_size)
        vd = (math.sqrt(3) * load_amps * length_m * (imp['r'] * 0.85 + imp['x'] * 0.52)) / 1000
        return round(vd, 2), round((vd / 400) * 100, 2)

# --- STREAMLIT UI ---
st.set_page_config(page_title="SG Pro Electrical", layout="wide")
engine = SGProEngine()

st.title("⚡ SG Pro: All-in-one Electrical Architecture")
tabs = st.tabs(["💡 Lighting Designer", "🔌 Cable Sizing", "📅 Asset Management"])

with tabs[0]:
    st.header("Automated Lighting Design")
    col1, col2 = st.columns(2)
    with col1:
        room = st.selectbox("Room Category", list(engine.lighting_standards.keys()))
        l = st.number_input("Length (m)", value=10.0)
        w = st.number_input("Width (m)", value=10.0)
    with col2:
        res = engine.calculate_lighting(room, l, w)
        st.metric("Fittings Required", f"{res['fittings']} units")
        st.info(f"Using: {res['details']['fitting_type']}")

with tabs[1]:
    st.header("Voltage Drop Calculator")
    c_size = st.selectbox("Select Cable (sqmm)", list(engine.cable_impedance.keys()))
    amps = st.number_input("Load (Amps)", value=20.0)
    dist = st.number_input("Distance (m)", value=30.0)
    v_drop, p_drop = engine.calculate_voltage_drop(amps, dist, c_size)
    st.metric("Voltage Drop", f"{v_drop}V ({p_drop}%)")

with tabs[2]:
    st.header("Predictive Maintenance")
    fig = go.Figure(go.Bar(x=list(engine.equipment_lifetime.keys()), y=list(engine.equipment_lifetime.values())))
    st.plotly_chart(fig)
