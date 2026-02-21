import streamlit as st
import math

# --- 1. CORE ENGINEERING ENGINE ---
class SingaporeElectricalLogic:
    def __init__(self):
        # AT (Ampere Trip) and AF (Ampere Frame) Mapping
        self.standard_frames = [63, 100, 125, 160, 250, 400, 630, 800, 1000, 1250, 1600, 2000, 2500, 3200, 4000]
        self.standard_trips = [6, 10, 16, 20, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 320, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3200, 4000]
        
        # Cable Iz (Current Capacity) for Cu/XLPE/SWA/PVC - Table 4E4A (SS 638)
        self.cable_db = {
            1.5: 25, 2.5: 33, 4: 43, 6: 56, 10: 77, 16: 102, 25: 135, 35: 166, 
            50: 201, 70: 255, 95: 309, 120: 358, 150: 410, 185: 469, 240: 551, 300: 627
        }
        # mV/A/m for XLPE cables (Table 4E4B)
        self.mv_am = {1.5: 31, 2.5: 19, 4: 12, 6: 7.9, 10: 4.7, 16: 2.9, 25: 1.9, 35: 1.35, 50: 1.05, 70: 0.75, 95: 0.58}

    def get_at_af(self, ib):
        at = next((x for x in self.standard_trips if x >= ib), 4000)
        af = next((x for x in self.standard_frames if x >= at), 4000)
        return at, af

    def calculate_vd(self, ib, length, size_sqmm, phase):
        mv = self.mv_am.get(size_sqmm, 0.4) # Default to 0.4 if size is very large
        vd = (mv * ib * length) / 1000
        limit = 400 * 0.04 if phase == "3-Phase" else 230 * 0.04
        return round(vd, 2), (vd <= limit)

# --- 2. STREAMLIT UI ---
st.set_page_config(page_title="SG Electrical Pro", layout="wide")
logic = SingaporeElectricalLogic()

st.title("🏗️ Professional Electrical Design Suite (Singapore Standards)")
st.markdown("Compliant with **SS 638**, **SS 535**, and **SP Group Guidelines**.")

tab1, tab2, tab3 = st.tabs(["🏗️ Cable & Breaker", "🏢 Switchroom Planning", "🔋 Essential Services"])

with tab1:
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.subheader("Input Parameters")
        p_kw = st.number_input("Design Load (kW)", value=50.0)
        phase = st.selectbox("System", ["1-Phase", "3-Phase"], index=1)
        dist = st.number_input("Route Length (m)", value=30)
        pf = 0.85
        
        ib = (p_kw * 1000) / (math.sqrt(3) * 400 * pf) if phase == "3-Phase" else (p_kw * 1000) / (230 * pf)
        at, af = logic.get_at_af(ib)
        
    with col2:
        st.subheader("Selection Results")
        b_type = "ACB" if af >= 800 else "MCCB" if af > 63 else "MCB"
        st.success(f"**Selected Breaker:** {at}AT / {af}AF {b_type}")
        
        # Cable Logic
        c_size = next((s for s, iz in logic.cable_db.items() if iz >= at), 300)
        vd_val, vd_pass = logic.calculate_vd(ib, dist, c_size, phase)
        
        st.info(f"**Recommended Cable:** {c_size} sqmm Cu/XLPE/SWA/PVC")
        if vd_pass:
            st.write(f"✅ Voltage Drop: {vd_val}V (Within 4% limit)")
        else:
            st.error(f"❌ Voltage Drop: {vd_val}V (Exceeds 4% limit! Up-size required)")



with tab2:
    st.subheader("📏 Switchboard & Room Sizing (Future Proof)")
    
    # Logic for space calculation
    # Typical panel widths: ACB=800mm, MCCB=400mm, Space for Meter=400mm
    msb_width = 800 if af >= 800 else 400
    if at > 100: msb_width += 400 # Add space for SP CT Metering
    
    total_width_with_spare = msb_width * 1.20 # 20% Future Expansion
    
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Estimated MSB Width (incl. 20% spare)", f"{total_width_with_spare:.0f} mm")
        st.write("**Maintenance Clearances:**")
        st.markdown("- **Front Clearance:** 800mm (Mandatory per SS 638)")
        st.markdown("- **Rear Clearance:** 600mm (If rear access required)")
        st.markdown("- **Door Opening:** 90° Minimum without obstruction")
        
    with c2:
        st.info("💡 **Future Proofing Tip:** Always ensure the switchroom ventilation can handle 20% more heat dissipation than current design.")



with tab3:
    st.subheader("🌍 Protection & Metering Stage")
    
    # Metering Placement
    if at <= 100:
        st.write("📍 **SP Metering:** Whole Current (Direct) Meter located before main switch.")
    else:
        st.write("📍 **SP Metering:** CT Metering required. Ensure a dedicated 400mm CT chamber is provided in the MSB.")
    
    # Earth Leakage
    if af >= 100:
        st.warning("🛡️ **Earth Leakage Relay (ELR):** Must install ELR + ZCT. Ensure the MCCB/ACB has a Shunt Trip coil.")
    else:
        st.write("🛡️ **RCCB:** Standard 30mA (Human Safety) or 300mA (Fire Protection) required.")
