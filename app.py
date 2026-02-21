import streamlit as st
import math
from datetime import datetime, timedelta

class SGElectricalProSuite:
    def __init__(self):
        # 1. BREAKER STANDARDS (AT/AF)
        self.standard_frames = [63, 100, 125, 160, 250, 400, 630, 800, 1000, 1250, 1600, 2000, 2500, 3200, 4000]
        self.standard_trips = [6, 10, 16, 20, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 320, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3200, 4000]
        
        # 2. CABLE DATA (SS 638 Table 4E4A - XLPE/SWA/Cu)
        self.cable_db = {
            1.5: 25, 2.5: 33, 4: 43, 6: 56, 10: 77, 16: 102, 25: 135, 35: 166, 
            50: 201, 70: 255, 95: 309, 120: 358, 150: 410, 185: 469, 240: 551, 300: 627,
            400: 750, 500: 860, 630: 980
        }
        
        # 3. MAINTENANCE FREQUENCY (Automation Stage)
        self.maintenance_logic = {
            "ACB": {"cycle": 1, "test": "Primary Injection / Contact Resistance"},
            "MCCB": {"cycle": 2, "test": "Secondary Injection / IR Scanning"},
            "MCB": {"cycle": 5, "test": "Visual & Trip Test"}
        }

    def get_at_af(self, ib):
        at = next((x for x in self.standard_trips if x >= ib), 4000)
        af = next((x for x in self.standard_frames if x >= at), 4000)
        return at, af

# --- APP INITIALIZATION ---
st.set_page_config(page_title="SG Electrical Design & Maintenance", layout="wide")
engine = SGElectricalProSuite()

st.title("⚡ SG Electrical Lifecycle Automation")
st.markdown("### Design ➡️ Installation ➡️ Maintenance")

# --- SIDEBAR INPUTS ---
with st.sidebar:
    st.header("📍 Project Parameters")
    load_kw = st.number_input("Design Load (kW)", value=150.0)
    dist = st.number_input("Cable Length (m)", value=40)
    install_date = st.date_input("Commissioning Date", datetime.now())
    st.divider()
    st.header("🏗️ MSB Configuration")
    sub_feeders = st.slider("Number of Outgoing Breakers", 1, 20, 5)
    spare_capacity = 0.20  # User Requirement: 20% Spare Space

# --- CALCULATIONS ---
ib = (load_kw * 1000) / (math.sqrt(3) * 400 * 0.85)
at, af = engine.get_at_af(ib)
b_type = "ACB" if af >= 800 else "MCCB" if af > 63 else "MCB"

# Sizing calculation (Approx 400mm width per panel + Incomer + Metering)
estimated_width = (800 if b_type == "ACB" else 400) + (sub_feeders * 400) + 400
total_msb_width = estimated_width * (1 + spare_capacity)

# --- TABBED INTERFACE ---
tab1, tab2, tab3 = st.tabs(["🏗️ Design & Sizing", "📐 Switchroom Clearances", "🛠️ Maintenance Automation"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Breaker Selection")
        st.metric("Design Current ($I_b$)", f"{ib:.2f} A")
        st.success(f"**Selected Incomer:** {at}AT / {af}AF {b_type}")
        
    with col2:
        st.subheader("Cable Selection")
        c_size = next((s for s, iz in engine.cable_db.items() if iz >= at), 630)
        st.info(f"**Main Cable:** {c_size} sqmm Cu/XLPE/SWA/PVC")
        st.write("*(Ensure Voltage Drop < 4% for future proofing)*")



with tab2:
    st.header("📐 Switchroom Space Planning (Statutory Requirements)")
    st.warning("⚠️ **Strict Maintenance Clearances Applied as per Singapore Standards:**")
    
    # Clearance Table
    clearance_data = {
        "Boundary": ["Front Clearance", "Rear Clearance", "Left Side", "Right Side", "Door Opening"],
        "Requirement": ["1500 mm", "800 mm", "800 mm", "800 mm", "90 Degree Minimum"],
        "Purpose": ["ACB Withdrawal / Maintenance", "Busbar Access", "Ventilation / Access", "Ventilation / Access", "Escape Route Compliance"]
    }
    st.table(clearance_data)
    
    st.subheader("Physical Footprint")
    c_a, c_b = st.columns(2)
    c_a.metric("Total MSB Length (Incl. 20% Spare)", f"{total_msb_width:.0f} mm")
    c_b.metric("Minimum Room Depth", f"{1500 + 800 + 800} mm", delta="Clearance Zones Only")



with tab3:
    st.header("🛠️ Maintenance Stage Online Management")
    
    # Automation: Schedule Next Service
    cycle_yrs = engine.maintenance_logic[b_type]["cycle"]
    next_service = install_date + timedelta(days=cycle_yrs * 365)
    
    col_x, col_y = st.columns(2)
    with col_x:
        st.subheader("Statutory Testing Schedule")
        st.metric("Next Mandatory Service", next_service.strftime('%d %B %Y'))
        st.write(f"**Required Test:** {engine.maintenance_logic[b_type]['test']}")
        
    with col_y:
        st.subheader("Maintenance Automation Checklist")
        st.checkbox("IR Thermography of Busbar Joints (Annual)")
        st.checkbox("Secondary Injection Test of Trip Units")
        st.checkbox("Verification of 1500mm Front Clearance (No storage encroachment)")



st.divider()
st.info("💡 **Developer Note:** This design tool ensures that from day one, the switchroom sizing is locked in to prevent 'Installation Stage' bottlenecks where equipment cannot be serviced due to tight spaces.")
