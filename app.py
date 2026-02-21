import streamlit as st
import math

class SGProEngine:
    def __init__(self):
        # Standard AT/AF Mapping
        self.standard_frames = [63, 100, 125, 160, 250, 400, 630, 800, 1000, 1250, 1600, 2000, 2500, 3200, 4000]
        self.standard_trips = [6, 10, 16, 20, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 320, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3200, 4000]
        
        # Cable Iz (Current Capacity) for Cu/XLPE/SWA/PVC - Table 4E4A (SS 638)
        self.cable_db = {
            1.5: 25, 2.5: 33, 4: 43, 6: 56, 10: 77, 16: 102, 25: 135, 35: 166, 
            50: 201, 70: 255, 95: 309, 120: 358, 150: 410, 185: 469, 240: 551, 300: 627
        }

    def get_at_af(self, ib):
        at = next((x for x in self.standard_trips if x >= ib), 4000)
        af = next((x for x in self.standard_frames if x >= at), 4000)
        return at, af

# --- UI SETUP ---
st.set_page_config(page_title="SG MSB Design Pro", layout="wide")
engine = SGProEngine()

st.title("⚡ Professional MSB Design & Space Planner")
st.subheader("Compliant with SS 638 & SP Group Guidelines")

with st.sidebar:
    st.header("1. Load Parameters")
    load_kw = st.number_input("Design Load (kW)", value=100.0)
    pf = st.slider("Power Factor", 0.7, 1.0, 0.85)
    voltage = 400 # Standard 3-Phase SG
    ib = (load_kw * 1000) / (math.sqrt(3) * voltage * pf)
    
    st.header("2. Switchboard Configuration")
    num_sub_feeders = st.number_input("Number of Outgoing Feeders", min_value=1, value=5)
    include_spare = st.checkbox("Include 20% Future Spare Space", value=True)

# --- CALCULATIONS ---
at, af = engine.get_at_af(ib)
b_type = "ACB" if af >= 800 else "MCCB" if af > 63 else "MCB"

# Sizing Estimation
# Incomer section + Sub-feeder sections + Metering Compartment
base_width = 800 if b_type == "ACB" else 600
sub_feeder_width = (num_sub_feeders * 400) # Avg 400mm per MCCB panel
metering_width = 400 if at > 100 else 0
total_width = base_width + sub_feeder_width + metering_width

if include_spare:
    total_width *= 1.2

# --- DISPLAY ---
col1, col2 = st.columns([1, 1])

with col1:
    st.info("### 📋 Breaker & Cable Schedule")
    st.metric("Design Current ($I_b$)", f"{ib:.2f} A")
    st.success(f"**Incomer:** {at}AT / {af}AF {b_type}")
    
    # Cable selection
    c_size = next((s for s, iz in engine.cable_db.items() if iz >= at), "Multiple Runs Required")
    st.write(f"**Main Incomer Cable:** {c_size} sqmm Cu/XLPE/SWA/PVC")
    
    st.divider()
    st.write("### 🛡️ Protection & Metering")
    if at > 100:
        st.error("📍 **Metering:** CT Metering required (Inside MSB CT Chamber)")
        st.warning("🛡️ **Earth Fault:** ELR + ZCT + Shunt Trip coil mandatory")
    else:
        st.write("📍 **Metering:** Whole Current Meter acceptable")
        st.write("🛡️ **Earth Fault:** RCCB (30mA for final power / 300mA for sub-mains)")



with col2:
    st.warning("### 📏 Switchroom Clearance Requirements")
    st.write("Based on Singapore Standards for Main Switchboards:")
    
    # Clearance Logic
    data = {
        "Position": ["Front (Maintenance/Withdrawal)", "Rear (Busbar Access)", "Left Side", "Right Side"],
        "Minimum Clearance": ["1500 mm", "800 mm", "800 mm", "800 mm"],
        "Purpose": ["ACB/Module withdrawal", "Access to terminations", "Ventilation/Access", "Ventilation/Access"]
    }
    st.table(data)
    
    st.write(f"**Estimated MSB Physical Length:** {total_width:.0f} mm")
    st.info(f"**Total Room Depth Required:** {1500 + 800 + 800} mm (Front + Board + Rear)")



st.divider()
st.subheader("💡 Design Notes for Installation Stage")
st.markdown("""
1. **Future Proofing:** The calculated width includes a **20% physical buffer** for additional switchgear.
2. **Door Swing:** Ensure all MSB doors can open to at least **90 degrees** without hitting walls or the 800mm clearance boundary.
3. **Ventilation:** Switchrooms must be mechanically ventilated or air-conditioned to maintain ambient temperatures below 35°C.
4. **Labelling:** All essential breakers (Generator/Fire) must be painted **Red** and clearly identified.
""")
