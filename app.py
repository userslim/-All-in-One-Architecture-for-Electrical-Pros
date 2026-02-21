import streamlit as st
import pandas
import math

# --- LOGIC ENGINE ---
class SingaporeElectricalLogic:
    def __init__(self):
        self.standard_breakers = [6, 10, 16, 20, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 320, 400, 630, 800, 1000, 1250, 1600, 2000, 2500, 3200, 4000]

    def get_design_current(self, kw, phase, voltage, pf):
        if phase == "1-Phase":
            return (kw * 1000) / (voltage * pf)
        return (kw * 1000) / (math.sqrt(3) * voltage * pf)

    def get_breaker(self, ib):
        for size in self.standard_breakers:
            if size >= ib: return size
        return None

    def get_protection_logic(self, load_type, breaker_size):
        if any(x in load_type.lower() for x in ["socket", "wet", "heater"]):
            return "30mA RCCB/RCBO (Mandatory - Human Protection)", "Type A or AC"
        if breaker_size > 63:
            return "ELR + ZCT (Earth Leakage Relay with Shunt Trip)", "Adjustable (e.g., 0.5A - 3A)"
        return "100mA/300mA RCCB (Fire Protection)", "Type AC"

# --- STREAMLIT UI ---
st.set_page_config(page_title="SG Electrical Design Pro", layout="wide")

st.title("⚡ SG Electrical Design Tool (SS 638 & SP Grid)")
st.markdown("Automated compliance tool for Singapore Power Grid standards.")

with st.sidebar:
    st.header("Input Parameters")
    load_kw = st.number_input("Total Load (kW)", min_value=0.1, value=10.0)
    phase = st.selectbox("Phase System", ["1-Phase", "3-Phase"], index=1)
    voltage = 230 if phase == "1-Phase" else 400
    pf = st.slider("Power Factor", 0.7, 1.0, 0.85)
    load_category = st.selectbox("Load Application", 
                                ["General Lighting/Power", "13A Sockets / Wet Area", "Main Switchboard (Incomer)", "Sub-Main Feeder"])

# Calculations
logic = SingaporeElectricalLogic()
ib = logic.get_design_current(load_kw, phase, voltage, pf)
in_breaker = logic.get_breaker(ib)

# 1. Breaker Type Selection
if in_breaker <= 63:
    b_type = "MCB (Miniature Circuit Breaker)"
elif in_breaker < 800:
    b_type = "MCCB (Molded Case Circuit Breaker)"
else:
    b_type = "ACB (Air Circuit Breaker)"

# 2. Protection & Metering Logic
prot_device, prot_sens = logic.get_protection_logic(load_category, in_breaker)
meter_type = "Whole Current (WC) Meter" if in_breaker <= 100 else "CT Metering"
meter_loc = "Before Main Switch (Meter Riser/Panel)" if in_breaker <= 100 else "Inside MSB (Dedicated CT Compartment)"

# --- DISPLAY RESULTS ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📋 Design Summary")
    st.metric("Design Current ($I_b$)", f"{ib:.2f} A")
    st.metric("Suggested Breaker Size ($I_n$)", f"{in_breaker} A")
    st.info(f"**Selected Breaker Type:** {b_type}")

with col2:
    st.subheader("🛡️ Protection & Compliance")
    st.success(f"**Earth Leakage:** {prot_device}")
    st.warning(f"**Sensitivity:** {prot_sens}")
    
st.divider()

st.subheader("📊 Singapore Power (SP) Metering Requirements")
st.write(f"Based on your load of **{in_breaker}A**, the following SP Group guidelines apply:")

table_data = {
    "Requirement": ["Meter Type", "Meter Location", "Standard Reference"],
    "Details": [meter_type, meter_loc, "SP Group Metering Handbook / SS 638"]
}
st.table(table_data)

st.caption("Note: Always verify with a Licensed Electrical Worker (LEW) for final submission.")
