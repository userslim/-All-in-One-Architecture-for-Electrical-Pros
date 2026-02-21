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
        
        # Typical motor starting multipliers
        self.motor_starting_multipliers = {
            "Lift (Variable Speed)": 2.5,
            "Lift (Star-Delta)": 3.0,
            "Fire Pump (Direct Online)": 6.0,
            "Fire Pump (Star-Delta)": 3.5,
            "Fire Pump (Soft Starter)": 2.5,
            "HVAC Chiller": 2.0,
            "Pressurization Fan": 3.0
        }

    def get_at_af(self, ib):
        at = next((x for x in self.standard_trips if x >= ib), 4000)
        af = next((x for x in self.standard_frames if x >= at), 4000)
        return at, af
    
    def calculate_generator_size(self, essential_loads, fire_loads, largest_motor_starting_kva):
        """
        Calculate required generator size based on running and starting loads
        """
        # Total running load (essential + fire loads during fire mode)
        total_running_kva = sum(essential_loads) + sum(fire_loads)
        
        # Starting scenario: Running loads + largest motor starting
        other_running_kva = total_running_kva - largest_motor_starting_kva  # Remove the motor's running load
        starting_scenario_kva = other_running_kva + largest_motor_starting_kva
        
        # Generator size with 20% safety margin
        required_gen_size = max(total_running_kva, starting_scenario_kva) * 1.2
        
        # Round up to nearest standard generator size (common sizes)
        standard_gen_sizes = [20, 30, 45, 60, 80, 100, 125, 150, 200, 250, 300, 400, 500, 630, 750, 800, 1000, 1250, 1500, 2000]
        recommended_gen = next((x for x in standard_gen_sizes if x >= required_gen_size), required_gen_size)
        
        return required_gen_size, recommended_gen, total_running_kva, starting_scenario_kva
    
    def calculate_earth_pits(self, has_fuel_tank=True, soil_condition="Normal"):
        """
        Recommend number of earth pits based on system requirements
        """
        earth_pits = {
            "generator_body": 2,  # Minimum 2 pits for generator body/neutral
            "fuel_tank": 1 if has_fuel_tank else 0,
            "lightning_arrestor": 1,  # If building has lightning protection
            "total_recommended": 0
        }
        
        # Additional pits for poor soil conditions
        if soil_condition == "Poor (High Resistance)":
            earth_pits["generator_body"] = 3
        
        earth_pits["total_recommended"] = earth_pits["generator_body"] + earth_pits["fuel_tank"] + earth_pits["lightning_arrestor"]
        
        return earth_pits
    
    def calculate_emergency_lights(self, total_lights, escape_route_lights_percent=100, general_area_percent=30):
        """
        Calculate number of lights to be connected to generator
        """
        emergency_lights = {
            "escape_route_lights": int(total_lights * 0.2 * (escape_route_lights_percent / 100)),  # Assuming 20% are escape route lights
            "general_area_lights": int(total_lights * 0.8 * (general_area_percent / 100)),  # Assuming 80% are general area
            "exit_signs": int(total_lights * 0.1)  # Assuming 10% are exit signs
        }
        
        emergency_lights["total_emergency_lights"] = emergency_lights["escape_route_lights"] + emergency_lights["general_area_lights"] + emergency_lights["exit_signs"]
        emergency_lights["emergency_load_watts"] = emergency_lights["total_emergency_lights"] * 10  # Assuming 10W LED per fitting
        
        return emergency_lights

# --- UI SETUP ---
st.set_page_config(page_title="SG MSB Design Pro", layout="wide")
engine = SGProEngine()

st.title("⚡ Professional MSB Design & Space Planner")
st.subheader("Compliant with SS 638 & SP Group Guidelines")

# Create tabs for better organization
tab1, tab2, tab3, tab4 = st.tabs(["📊 Main MSB Design", "🔄 Generator & Emergency Systems", "⛓️ Earthing Design", "💡 Emergency Lighting"])

with st.sidebar:
    st.header("1. Load Parameters")
    load_kw = st.number_input("Design Load (kW)", value=100.0)
    pf = st.slider("Power Factor", 0.7, 1.0, 0.85)
    voltage = 400 # Standard 3-Phase SG
    ib = (load_kw * 1000) / (math.sqrt(3) * voltage * pf)
    
    st.header("2. Switchboard Configuration")
    num_sub_feeders = st.number_input("Number of Outgoing Feeders", min_value=1, value=5)
    include_spare = st.checkbox("Include 20% Future Spare Space", value=True)

# --- TAB 1: MAIN MSB DESIGN ---
with tab1:
    # --- CALCULATIONS ---
    at, af = engine.get_at_af(ib)
    b_type = "ACB" if af >= 800 else "MCCB" if af > 63 else "MCB"

    # Sizing Estimation
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

# --- TAB 2: GENERATOR & EMERGENCY SYSTEMS ---
with tab2:
    st.header("🔄 Generator Sizing for Essential & Fire Services")
    st.write("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Essential Loads (Must Run During Power Outage)")
        
        # Lift inputs
        st.write("**🚡 Lift Motors (Homing Function)**")
        num_lifts = st.number_input("Number of Lifts", min_value=0, value=2, key="num_lifts")
        lift_loads = []
        lift_starting_kvas = []
        
        for i in range(num_lifts):
            lift_kw = st.number_input(f"Lift {i+1} Motor (kW)", value=10.0, key=f"lift_{i}_kw")
            lift_pf = st.slider(f"Lift {i+1} Power Factor", 0.7, 1.0, 0.85, key=f"lift_{i}_pf")
            lift_type = st.selectbox(f"Lift {i+1} Starting Type", 
                                    ["Lift (Variable Speed)", "Lift (Star-Delta)"], 
                                    key=f"lift_{i}_type")
            
            running_kva = (lift_kw * 1000) / (math.sqrt(3) * voltage * lift_pf) / 1000  # Convert to kVA
            starting_multiplier = engine.motor_starting_multipliers[lift_type]
            starting_kva = running_kva * starting_multiplier
            
            lift_loads.append(running_kva)
            lift_starting_kvas.append(starting_kva)
            
            st.caption(f"  Running: {running_kva:.1f} kVA | Starting: {starting_kva:.1f} kVA")
        
        # Other essential loads
        st.write("**🏢 Other Essential Loads**")
        num_essential = st.number_input("Number of Other Essential Loads", min_value=0, value=2, key="num_essential")
        essential_loads = lift_loads.copy()
        
        for i in range(num_essential):
            load_desc = st.text_input(f"Load {i+1} Description", value=f"Essential Load {i+1}", key=f"ess_desc_{i}")
            load_kva = st.number_input(f"{load_desc} (kVA)", value=5.0, key=f"ess_load_{i}")
            essential_loads.append(load_kva)
    
    with col2:
        st.subheader("🔥 Fire Fighting Loads (Must Run During Fire)")
        
        # Fire pump inputs
        st.write("**🚒 Fire Pump System**")
        has_fire_pump = st.checkbox("Include Fire Pump", value=True)
        
        fire_loads = []
        fire_starting_kvas = []
        
        if has_fire_pump:
            main_pump_kw = st.number_input("Main Fire Pump Motor (kW)", value=30.0)
            main_pump_pf = st.slider("Main Fire Pump PF", 0.7, 1.0, 0.85, key="main_pump_pf")
            pump_type = st.selectbox("Fire Pump Starting Type", 
                                    ["Fire Pump (Direct Online)", "Fire Pump (Star-Delta)", "Fire Pump (Soft Starter)"])
            
            running_kva = (main_pump_kw * 1000) / (math.sqrt(3) * voltage * main_pump_pf) / 1000
            starting_multiplier = engine.motor_starting_multipliers[pump_type]
            starting_kva = running_kva * starting_multiplier
            
            fire_loads.append(running_kva)
            fire_starting_kvas.append(starting_kva)
            
            st.caption(f"  Running: {running_kva:.1f} kVA | Starting: {starting_kva:.1f} kVA")
            
            # Jockey pump
            has_jockey = st.checkbox("Include Jockey Pump", value=True)
            if has_jockey:
                jockey_kw = st.number_input("Jockey Pump Motor (kW)", value=2.2)
                jockey_pf = st.slider("Jockey Pump PF", 0.7, 1.0, 0.85, key="jockey_pf")
                jockey_running = (jockey_kw * 1000) / (math.sqrt(3) * voltage * jockey_pf) / 1000
                fire_loads.append(jockey_running)
                st.caption(f"  Jockey Pump Running: {jockey_running:.1f} kVA")
        
        # Pressurization fans
        st.write("**💨 Staircase Pressurization Fans**")
        num_fans = st.number_input("Number of Pressurization Fans", min_value=0, value=2, key="num_fans")
        
        for i in range(num_fans):
            fan_kw = st.number_input(f"Fan {i+1} Motor (kW)", value=5.5, key=f"fan_{i}_kw")
            fan_pf = st.slider(f"Fan {i+1} PF", 0.7, 1.0, 0.85, key=f"fan_{i}_pf")
            fan_running = (fan_kw * 1000) / (math.sqrt(3) * voltage * fan_pf) / 1000
            fire_loads.append(fan_running)
    
    # Generator calculation
    st.write("---")
    st.subheader("📊 Generator Sizing Results")
    
    # Find largest starting load
    all_starting_kvas = lift_starting_kvas + fire_starting_kvas
    largest_starting_kva = max(all_starting_kvas) if all_starting_kvas else 0
    
    required_gen, recommended_gen, running_kva, starting_kva = engine.calculate_generator_size(
        essential_loads, fire_loads, largest_starting_kva
    )
    
    col3, col4, col5 = st.columns(3)
    with col3:
        st.metric("Total Running Load", f"{running_kva:.1f} kVA")
    with col4:
        st.metric("Worst-Case Starting Load", f"{starting_kva:.1f} kVA")
    with col5:
        st.metric("Recommended Generator", f"{recommended_gen:.0f} kVA")
    
    st.success(f"✅ **Final Recommendation:** Select a **{recommended_gen:.0f} kVA** generator (Prime Rating) to handle all essential and fire loads with proper starting capability.")

# --- TAB 3: EARTHING DESIGN ---
with tab3:
    st.header("⛓️ Earthing System Design")
    st.write("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Earth Pit Configuration")
        
        has_fuel_tank = st.checkbox("Separate Fuel Tank Present", value=True)
        soil_condition = st.selectbox("Soil Condition", ["Normal", "Poor (High Resistance)"])
        
        earth_pits = engine.calculate_earth_pits(has_fuel_tank, soil_condition)
        
        st.write("**Recommended Earth Pits:**")
        st.write(f"- Generator Body/Neutral: **{earth_pits['generator_body']} pits**")
        if earth_pits['fuel_tank'] > 0:
            st.write(f"- Fuel Tank: **{earth_pits['fuel_tank']} pit**")
        st.write(f"- Lightning Arrestor: **{earth_pits['lightning_arrestor']} pit**")
        st.write(f"**Total Earth Pits Required: {earth_pits['total_recommended']}**")
        
        st.info("ℹ️ Earth pits should be interconnected to form a common earth busbar with resistance < 1Ω.")
    
    with col2:
        st.subheader("Test Link Point Requirements")
        
        st.write("**🔧 Test Link Configuration:**")
        st.markdown("""
        - Install a **bolted removable link** in the main earthing conductor
        - Location: Between generator neutral and main earth electrode
        - Purpose: Allows isolation for earth resistance testing
        - Specification: Copper link rated for fault current (minimum 25x6mm copper bar)
        """)
        
        st.warning("**⚠️ Important:**")
        st.markdown("""
        - Test link must be accessible only to authorized personnel
        - Clear labeling required: "EARTH TEST LINK - DO NOT REMOVE WITHOUT AUTHORIZATION"
        - Include in maintenance schedule for periodic testing
        """)

# --- TAB 4: EMERGENCY LIGHTING ---
with tab4:
    st.header("💡 Emergency Lighting Design")
    st.write("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Lighting Inventory")
        
        total_lights = st.number_input("Total Number of Light Fittings in Building", min_value=1, value=200)
        
        st.write("**Connection Strategy:**")
        escape_percent = st.slider("Escape Route Lights (% to connect)", 0, 100, 100)
        general_percent = st.slider("General Area Lights (% to connect)", 0, 100, 30)
        
        emergency_calc = engine.calculate_emergency_lights(total_lights, escape_percent, general_percent)
        
        st.write("**Results:**")
        st.write(f"- Escape Route Lights on Gen: **{emergency_calc['escape_route_lights']}**")
        st.write(f"- General Area Lights on Gen: **{emergency_calc['general_area_lights']}**")
        st.write(f"- Exit Signs on Gen: **{emergency_calc['exit_signs']}**")
        st.write(f"- **Total Emergency Lights: {emergency_calc['total_emergency_lights']}**")
        
        st.metric("Estimated Emergency Lighting Load", f"{emergency_calc['emergency_load_watts']/1000:.2f} kW")
    
    with col2:
        st.subheader("Generator Connection Requirements")
        
        st.markdown("""
        **🔌 Connection Methods:**
        
        1. **Dedicated Emergency Lighting Busbar**
           - All emergency lights connected to dedicated section in MSB/DB
           - Automatically transfers to generator on mains failure
        
        2. **Contactor Control**
           - Standard lights controlled by contactors
           - Selected circuits switched to generator during outage
        
        **📋 Design Checklist:**
        """)
        
        st.checkbox("Emergency lights on separate final circuits", value=True, disabled=True)
        st.checkbox("Exit signs maintained (always on)", value=True, disabled=True)
        st.checkbox("Minimum 1 lux on escape routes", value=True, disabled=True)
        st.checkbox("Emergency lighting test facilities provided", value=True, disabled=True)
        st.checkbox("Green dot/EM marking on fittings", value=True, disabled=True)
        
        st.info("ℹ️ For Singapore: Comply with SS 563 & Fire Code requirements for emergency lighting.")

# --- GLOBAL DESIGN NOTES ---
st.divider()
st.subheader("💡 Design Notes for Installation Stage")
col_note1, col_note2 = st.columns(2)

with col_note1:
    st.markdown("""
    **General Requirements:**
    1. **Future Proofing:** The calculated width includes a **20% physical buffer** for additional switchgear.
    2. **Door Swing:** Ensure all MSB doors can open to at least **90 degrees** without hitting walls.
    3. **Ventilation:** Switchrooms must maintain ambient temperatures below 35°C.
    4. **Labelling:** All essential breakers (Generator/Fire) must be painted **Red** and clearly identified.
    """)

with col_note2:
    st.markdown("""
    **Generator Room Requirements:**
    1. **Ventilation:** Provide adequate air intake/exhaust for generator cooling.
    2. **Fuel Storage:** Day tank minimum 8-hour runtime, main tank based on building requirements.
    3. **Acoustic Treatment:** Consider noise levels for residential neighbors.
    4. **Maintenance Access:** Minimum 1m clearance around generator set.
    """)
