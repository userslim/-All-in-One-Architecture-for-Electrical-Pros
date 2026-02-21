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
            50: 201, 70: 255, 95: 309, 120: 358, 150: 410, 185: 469, 240: 551, 300: 627,
            400: 750, 500: 860, 630: 980  # Additional larger cables
        }
        
        # Cable resistance and reactance (Ohms/km) for voltage drop calculation
        # Based on typical Cu/XLPE cables
        self.cable_impedance = {
            1.5: {"r": 14.8, "x": 0.145},
            2.5: {"r": 8.91, "x": 0.135},
            4: {"r": 5.57, "x": 0.125},
            6: {"r": 3.71, "x": 0.120},
            10: {"r": 2.24, "x": 0.115},
            16: {"r": 1.41, "x": 0.110},
            25: {"r": 0.889, "x": 0.105},
            35: {"r": 0.641, "x": 0.100},
            50: {"r": 0.473, "x": 0.100},
            70: {"r": 0.328, "x": 0.095},
            95: {"r": 0.236, "x": 0.095},
            120: {"r": 0.188, "x": 0.090},
            150: {"r": 0.153, "x": 0.090},
            185: {"r": 0.124, "x": 0.090},
            240: {"r": 0.0991, "x": 0.085},
            300: {"r": 0.0795, "x": 0.085},
            400: {"r": 0.0625, "x": 0.085},
            500: {"r": 0.0495, "x": 0.085},
            630: {"r": 0.0395, "x": 0.085}
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
        
        # Lightning protection standards (Based on SS 555 / IEC 62305)
        self.lightning_protection_levels = {
            "Level I": {"protection_angle": 20, "mesh_size": 5, "rolling_sphere": 20, "risk_level": "Very High (e.g., explosives)"},
            "Level II": {"protection_angle": 25, "mesh_size": 10, "rolling_sphere": 30, "risk_level": "High (e.g., hospitals, tall buildings)"},
            "Level III": {"protection_angle": 35, "mesh_size": 15, "rolling_sphere": 45, "risk_level": "Normal (e.g., commercial buildings)"},
            "Level IV": {"protection_angle": 45, "mesh_size": 20, "rolling_sphere": 60, "risk_level": "Low (e.g., temporary structures)"}
        }
        
        # Air terminal spacing based on protection level and height
        self.air_terminal_spacing = {
            "Level I": {"low": 5, "medium": 4, "high": 3},
            "Level II": {"low": 8, "medium": 6, "high": 4},
            "Level III": {"low": 10, "medium": 8, "high": 5},
            "Level IV": {"low": 12, "medium": 10, "high": 6}
        }
        
        # Maintenance schedules (months)
        self.maintenance_schedule = {
            "daily": ["Generator visual check", "Battery charger status", "Fuel level", "Alarm status"],
            "weekly": ["Generator run test (30 mins)", "Battery voltage check", "Coolant level", "Oil level"],
            "monthly": ["Load bank test", "Earth resistance measurement", "Emergency lighting test", "Fire pump test"],
            "quarterly": ["Cable thermal imaging", "Connection torque check", "Insulation resistance test", "Protection relay test"],
            "annually": ["Full load generator test", "Battery replacement", "Oil and filter change", "Professional inspection"]
        }
        
        # Common issues and solutions
        self.troubleshooting_guide = {
            "Generator fails to start": ["Check battery voltage", "Check fuel level", "Check control fuse", "Check emergency stop"],
            "Voltage drop issues": ["Check cable sizing", "Check connections", "Check load balance", "Consider cable upgrade"],
            "Earth fault trip": ["Check insulation resistance", "Check for moisture", "Check RCCB/ELR", "Identify faulty circuit"],
            "Overheating cables": ["Check load current", "Check ventilation", "Check connections", "Derate or upgrade cable"]
        }

    def get_at_af(self, ib):
        at = next((x for x in self.standard_trips if x >= ib), 4000)
        af = next((x for x in self.standard_frames if x >= at), 4000)
        return at, af
    
    def calculate_voltage_drop(self, cable_size, current, length, pf=0.85):
        """
        Calculate voltage drop for given cable size and length
        Returns voltage drop in volts and percentage
        """
        if cable_size not in self.cable_impedance:
            return None, None
        
        impedance = self.cable_impedance[cable_size]
        
        # Voltage drop formula for 3-phase: Vd = √3 × I × L × (R cosφ + X sinφ) / 1000
        sin_phi = math.sqrt(1 - pf**2)
        v_drop_per_km = math.sqrt(3) * current * (impedance["r"] * pf + impedance["x"] * sin_phi)
        v_drop = v_drop_per_km * length / 1000
        
        v_drop_percent = (v_drop / 400) * 100  # Assuming 400V system
        
        return v_drop, v_drop_percent
    
    def select_cable_with_vd(self, ib, length, pf=0.85, max_vd_percent=4):
        """
        Select cable size considering both current capacity and voltage drop
        """
        # First find cables that meet current capacity
        suitable_cables = []
        for size, iz in self.cable_db.items():
            if iz >= ib * 1.25:  # 25% safety margin for continuous load
                vd, vd_percent = self.calculate_voltage_drop(size, ib, length, pf)
                if vd_percent and vd_percent <= max_vd_percent:
                    suitable_cables.append({
                        "size": size,
                        "iz": iz,
                        "vd": vd,
                        "vd_percent": vd_percent
                    })
        
        if suitable_cables:
            # Return the smallest cable that meets both requirements
            return min(suitable_cables, key=lambda x: x["size"])
        else:
            # If no cable meets VD requirement, return largest that meets current capacity
            current_suitable = [{"size": s, "iz": iz} for s, iz in self.cable_db.items() if iz >= ib * 1.25]
            if current_suitable:
                largest = max(current_suitable, key=lambda x: x["size"])
                vd, vd_percent = self.calculate_voltage_drop(largest["size"], ib, length, pf)
                return {
                    "size": largest["size"],
                    "iz": largest["iz"],
                    "vd": vd,
                    "vd_percent": vd_percent,
                    "warning": f"Voltage drop ({vd_percent:.2f}%) exceeds recommended 4%"
                }
            else:
                return {"error": "No cable found. Multiple runs required."}
    
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
    
    def calculate_earth_pits(self, has_fuel_tank=True, soil_condition="Normal", building_area=0, protection_level="Level III"):
        """
        Recommend number of earth pits based on system requirements including lightning protection
        """
        # Base earth pits for generator
        earth_pits = {
            "generator_body": 2,  # Minimum 2 pits for generator body/neutral
            "fuel_tank": 1 if has_fuel_tank else 0,
            "lightning_protection": 0,  # Will be calculated based on area
            "total_recommended": 0
        }
        
        # Additional pits for poor soil conditions
        if soil_condition == "Poor (High Resistance)":
            earth_pits["generator_body"] = 3
        
        # Calculate lightning protection earth pits based on building area
        if building_area > 0:
            # SS 555 / IEC 62305 requirements for lightning protection earthing
            if building_area <= 500:
                earth_pits["lightning_protection"] = 2  # Small building
            elif building_area <= 2000:
                earth_pits["lightning_protection"] = 4  # Medium building
            elif building_area <= 5000:
                earth_pits["lightning_protection"] = 6  # Large building
            else:
                earth_pits["lightning_protection"] = 8 + math.ceil((building_area - 5000) / 2000)  # Additional pits for very large buildings
            
            # Adjust based on protection level
            level_multiplier = {
                "Level I": 1.5,   # More stringent requirements
                "Level II": 1.2,
                "Level III": 1.0,
                "Level IV": 0.8
            }
            earth_pits["lightning_protection"] = math.ceil(earth_pits["lightning_protection"] * level_multiplier[protection_level])
        
        earth_pits["total_recommended"] = earth_pits["generator_body"] + earth_pits["fuel_tank"] + earth_pits["lightning_protection"]
        
        return earth_pits
    
    def calculate_lightning_protection(self, building_length, building_width, building_height, protection_level="Level III", roof_type="Flat"):
        """
        Calculate lightning protection requirements based on building dimensions
        """
        building_area = building_length * building_width
        perimeter = 2 * (building_length + building_width)
        
        # Calculate number of air terminals based on protection level and building dimensions
        spacing = self.air_terminal_spacing[protection_level]
        
        # Determine height category for spacing
        if building_height < 10:
            height_category = "low"
        elif building_height < 20:
            height_category = "medium"
        else:
            height_category = "high"
        
        terminal_spacing = spacing[height_category]
        
        # Calculate number of air terminals along length and width
        terminals_length = math.ceil(building_length / terminal_spacing) + 1
        terminals_width = math.ceil(building_width / terminal_spacing) + 1
        
        # For flat roofs, terminals are placed in a grid pattern
        if roof_type == "Flat":
            num_air_terminals = terminals_length * terminals_width
        else:  # Pitched roof
            # For pitched roofs, terminals along ridge and edges
            num_air_terminals = terminals_length * 2 + terminals_width
        
        # Calculate down conductors based on perimeter
        # SS 555 requires down conductors every 20m along perimeter
        num_down_conductors = max(2, math.ceil(perimeter / 20))
        
        # Calculate test joints (one per down conductor at ground level)
        num_test_joints = num_down_conductors
        
        # Calculate roof conductors (mesh network)
        roof_conductor_length = (terminals_length - 1) * building_width + (terminals_width - 1) * building_length
        
        # Calculate total conductor length
        down_conductor_length = num_down_conductors * building_height * 2  # Up and down
        total_conductor_length = roof_conductor_length + down_conductor_length
        
        protection_params = self.lightning_protection_levels[protection_level]
        
        return {
            "building_area": building_area,
            "perimeter": perimeter,
            "num_air_terminals": num_air_terminals,
            "num_down_conductors": num_down_conductors,
            "num_test_joints": num_test_joints,
            "roof_conductor_length": roof_conductor_length,
            "down_conductor_length": down_conductor_length,
            "total_conductor_length": total_conductor_length,
            "protection_angle": protection_params["protection_angle"],
            "mesh_size": protection_params["mesh_size"],
            "rolling_sphere_radius": protection_params["rolling_sphere"],
            "terminal_spacing": terminal_spacing
        }
    
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
    
    def generate_design_checklist(self):
        """Generate comprehensive design stage checklist"""
        return {
            "Load Assessment": [
                "✓ Calculate total connected load",
                "✓ Determine diversity factors",
                "✓ Identify essential and non-essential loads",
                "✓ Calculate peak demand",
                "✓ Consider future expansion (20% spare)"
            ],
            "Equipment Selection": [
                "✓ Main breaker sizing (AT/AF selection)",
                "✓ Cable sizing (current capacity + voltage drop)",
                "✓ Generator sizing (running + starting loads)",
                "✓ UPS sizing for critical loads",
                "✓ Surge protection device selection"
            ],
            "Protection Coordination": [
                "✓ Earth fault protection coordination",
                "✓ Short circuit protection coordination",
                "✓ Discrimination study for breakers",
                "✓ Arc flash risk assessment",
                "✓ Selectivity between main and sub-main"
            ],
            "Earthing System": [
                "✓ Earth pit locations and quantity",
                "✓ Earth resistance target (<1Ω)",
                "✓ Test link points identification",
                "✓ Equipotential bonding requirements",
                "✓ Lightning protection integration"
            ],
            "Compliance Checks": [
                "✓ SS 638 (Electrical installation)",
                "✓ SS 555 (Lightning protection)",
                "✓ Fire Code requirements",
                "✓ SP Group technical requirements",
                "✓ BCA approval requirements"
            ]
        }
    
    def generate_installation_checklist(self):
        """Generate comprehensive installation stage checklist"""
        return {
            "Pre-Installation": [
                "✓ Site inspection and verification",
                "✓ Material delivery inspection",
                "✓ Storage condition check",
                "✓ Installation method statement review",
                "✓ Safety permit requirements"
            ],
            "Cable Installation": [
                "✓ Cable route verification",
                "✓ Cable tray/ladder installation",
                "✓ Proper cable segregation (LV, ELV, control)",
                "✓ Cable pulling tension monitoring",
                "✓ Minimum bending radius compliance",
                "✓ Cable glanding and termination",
                "✓ Cable identification and labeling"
            ],
            "Switchgear Installation": [
                "✓ Switchgear positioning and leveling",
                "✓ Busbar connection torque check",
                "✓ Compartment cleanliness verification",
                "✓ Door alignment and operation",
                "✓ Ventilation requirements",
                "✓ Clearance space verification"
            ],
            "Generator Installation": [
                "✓ Base/foundation verification",
                "✓ Anti-vibration mount installation",
                "✓ Fuel line connection and testing",
                "✓ Exhaust system installation",
                "✓ Cooling system connection",
                "✓ Battery and charger installation",
                "✓ ATS installation and wiring"
            ],
            "Testing & Commissioning": [
                "✓ Insulation resistance test",
                "✓ Continuity test",
                "✓ Polarity check",
                "✓ Phase sequence verification",
                "✓ Earth resistance measurement",
                "✓ Functional testing of all breakers",
                "✓ Protection relay testing",
                "✓ Generator load bank testing",
                "✓ Transfer switch operation test"
            ]
        }
    
    def generate_maintenance_checklist(self):
        """Generate comprehensive maintenance stage checklist"""
        return {
            "Daily": [
                "✓ Generator visual inspection",
                "✓ Battery charger status check",
                "✓ Fuel level verification",
                "✓ Alarm panel status check",
                "✓ Switchroom temperature check"
            ],
            "Weekly": [
                "✓ Generator no-load run (30 minutes)",
                "✓ Battery voltage measurement",
                "✓ Coolant level check",
                "✓ Engine oil level check",
                "✓ Emergency lighting test",
                "✓ Fire pump test run"
            ],
            "Monthly": [
                "✓ Earth resistance measurement",
                "✓ Load bank test (if applicable)",
                "✓ Circuit breaker exercise",
                "✓ Visual inspection of cables",
                "✓ ATS operation test",
                "✓ UPS battery test"
            ],
            "Quarterly": [
                "✓ Thermal imaging of connections",
                "✓ Torque check of all connections",
                "✓ Insulation resistance test",
                "✓ Protection relay calibration",
                "✓ Battery load test",
                "✓ Fuel system check"
            ],
            "Annually": [
                "✓ Full load generator test",
                "✓ Battery replacement (if needed)",
                "✓ Oil and filter change",
                "✓ Coolant replacement",
                "✓ Air filter replacement",
                "✓ Professional inspection",
                "✓ Comprehensive system report"
            ],
            "5 Years": [
                "✓ Cable replacement (if deteriorated)",
                "✓ Switchgear overhaul",
                "✓ Generator major overhaul",
                "✓ Lightning protection system audit",
                "✓ Earthing system upgrade (if needed)"
            ]
        }
    
    def generate_troubleshooting_guide(self):
        """Generate troubleshooting guide for common issues"""
        return {
            "Generator Issues": {
                "Fails to start": [
                    "Check battery voltage (min 12.5V)",
                    "Check fuel level and quality",
                    "Check emergency stop button",
                    "Check control panel fuses",
                    "Check starter motor connections"
                ],
                "Runs but no output": [
                    "Check AVR connections",
                    "Check excitation system",
                    "Check output breaker",
                    "Check voltage regulator",
                    "Check for tripped protection"
                ],
                "Overheating": [
                    "Check cooling system",
                    "Check radiator fins",
                    "Check coolant level",
                    "Check load level",
                    "Check ambient temperature"
                ]
            },
            "Switchgear Issues": {
                "Breaker trips frequently": [
                    "Check for overload condition",
                    "Check for short circuit",
                    "Check insulation resistance",
                    "Check earth fault",
                    "Check breaker calibration"
                ],
                "Overheating at connections": [
                    "Check torque of connections",
                    "Check for loose terminations",
                    "Check load current",
                    "Thermal imaging required",
                    "Consider cable upgrade"
                ]
            },
            "Cable Issues": {
                "Voltage drop problems": [
                    "Verify actual cable length",
                    "Check actual load current",
                    "Check power factor",
                    "Consider cable upgrade",
                    "Check for loose connections"
                ],
                "Insulation failure": [
                    "Check for moisture ingress",
                    "Check for mechanical damage",
                    "Check termination quality",
                    "Megger test required",
                    "Consider cable replacement"
                ]
            },
            "Earth Faults": {
                "RCCB/ELR trips": [
                    "Identify faulty circuit",
                    "Check insulation resistance",
                    "Check for moisture",
                    "Check connected equipment",
                    "Verify earth continuity"
                ]
            }
        }

# --- UI SETUP ---
st.set_page_config(page_title="SG MSB Design Pro", layout="wide")
engine = SGProEngine()

st.title("⚡ Professional MSB Design & Space Planner")
st.subheader("Compliant with SS 638, SP Group & SS 555 Lightning Protection Guidelines")

# Create tabs for better organization
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📊 Main MSB Design", 
    "🔄 Generator & Emergency Systems", 
    "⛓️ Earthing Design", 
    "⚡ Lightning Protection", 
    "💡 Emergency Lighting",
    "📋 Design Stage",
    "🔧 Installation Stage",
    "🛠️ Maintenance & Troubleshooting"
])

with st.sidebar:
    st.header("1. Load Parameters")
    load_kw = st.number_input("Design Load (kW)", value=100.0)
    pf = st.slider("Power Factor", 0.7, 1.0, 0.85)
    voltage = 400 # Standard 3-Phase SG
    ib = (load_kw * 1000) / (math.sqrt(3) * voltage * pf)
    
    st.header("2. Cable Run Information")
    cable_length = st.number_input("Cable Length from Source to Load (m)", min_value=1.0, value=50.0)
    max_vd_percent = st.slider("Maximum Allowed Voltage Drop (%)", 1.0, 8.0, 4.0, 0.5)
    
    st.header("3. Switchboard Configuration")
    num_sub_feeders = st.number_input("Number of Outgoing Feeders", min_value=1, value=5)
    include_spare = st.checkbox("Include 20% Future Spare Space", value=True)
    
    st.header("4. Building Information")
    st.subheader("For Lightning Protection")
    building_length = st.number_input("Building Length (m)", min_value=1.0, value=50.0)
    building_width = st.number_input("Building Width (m)", min_value=1.0, value=30.0)
    building_height = st.number_input("Building Height (m)", min_value=1.0, value=15.0)
    roof_type = st.selectbox("Roof Type", ["Flat", "Pitched"])
    protection_level = st.selectbox("Lightning Protection Level", 
                                   ["Level I", "Level II", "Level III", "Level IV"], 
                                   index=2)  # Default to Level III

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
        
        # Cable selection with voltage drop consideration
        cable_result = engine.select_cable_with_vd(ib, cable_length, pf, max_vd_percent)
        
        if "error" in cable_result:
            st.error(f"⚠️ {cable_result['error']}")
        else:
            st.write(f"**Main Incomer Cable:** {cable_result['size']} sqmm Cu/XLPE/SWA/PVC")
            st.write(f"**Current Capacity (Iz):** {cable_result['iz']} A")
            
            # Voltage drop display with color coding
            vd_color = "🟢" if cable_result['vd_percent'] <= max_vd_percent else "🔴"
            st.write(f"**Voltage Drop:** {vd_color} {cable_result['vd']:.2f} V ({cable_result['vd_percent']:.2f}%)")
            
            if "warning" in cable_result:
                st.warning(f"⚠️ {cable_result['warning']}")
            
            # Recommendation for long runs
            if cable_length > 100:
                st.info("💡 **Tip:** For runs >100m, consider increasing cable size or installing a sub-distribution board to reduce voltage drop.")
        
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
        
        # Cable routing considerations
        st.subheader("🔌 Cable Routing Considerations")
        st.markdown("""
        - **Minimum bending radius:** 12-15× cable diameter
        - **Cable tray fill:** Max 40% for future cables
        - **Segregation:** Separate power, control, and data cables
        - **Fire stopping:** Required at floor/wall penetrations
        - **Support spacing:** Every 300mm for vertical, 600mm for horizontal
        """)

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
    
    # Generator cable sizing
    st.subheader("🔌 Generator Cable Sizing")
    gen_current = (recommended_gen * 1000) / (math.sqrt(3) * voltage)
    gen_cable_length = st.number_input("Generator to MSB Cable Length (m)", value=20.0, key="gen_cable_length")
    
    gen_cable = engine.select_cable_with_vd(gen_current, gen_cable_length, pf=0.8, max_vd_percent=3)
    
    if "error" not in gen_cable:
        st.write(f"**Generator Cable:** {gen_cable['size']} sqmm Cu/XLPE/SWA/PVC (4-core)")
        st.write(f"**Voltage Drop:** {gen_cable['vd']:.2f} V ({gen_cable['vd_percent']:.2f}%)")
    else:
        st.error("Multiple cable runs required for generator connection")

# --- TAB 3: EARTHING DESIGN ---
with tab3:
    st.header("⛓️ Earthing System Design")
    st.write("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Earth Pit Configuration")
        
        has_fuel_tank = st.checkbox("Separate Fuel Tank Present", value=True)
        soil_condition = st.selectbox("Soil Condition", ["Normal", "Poor (High Resistance)"])
        building_area = building_length * building_width
        
        st.info(f"**Building Area:** {building_area:.0f} m²")
        
        earth_pits = engine.calculate_earth_pits(has_fuel_tank, soil_condition, building_area, protection_level)
        
        st.write("**Recommended Earth Pits:**")
        st.write(f"- Generator Body/Neutral: **{earth_pits['generator_body']} pits**")
        if earth_pits['fuel_tank'] > 0:
            st.write(f"- Fuel Tank: **{earth_pits['fuel_tank']} pit**")
        st.write(f"- Lightning Protection System: **{earth_pits['lightning_protection']} pits**")
        st.write(f"**Total Earth Pits Required: {earth_pits['total_recommended']}**")
        
        st.info("ℹ️ Earth pits should be interconnected to form a common earth busbar with resistance < 1Ω.")
        
        # Earth pit specification
        st.subheader("🔧 Earth Pit Specification")
        st.markdown("""
        **Standard Earth Pit Requirements:**
        - Depth: Minimum 3 meters
        - Electrode: Copper-clad steel rod (20mm diameter)
        - Backfill: Bentonite mix or earth enhancement compound
        - Cover: Heavy-duty cast iron with locking arrangement
        - Test link: Removable link for resistance testing
        """)
    
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
        
        # Earth resistance requirements
        st.subheader("📊 Earth Resistance Requirements")
        resistance_data = {
            "System": ["Generator Neutral", "Lightning Protection", "Fuel Tank", "Combined System"],
            "Max Resistance": ["1 Ω", "10 Ω", "10 Ω", "1 Ω"]
        }
        st.table(resistance_data)

# --- TAB 4: LIGHTNING PROTECTION ---
with tab4:
    st.header("⚡ Lightning Protection System Design")
    st.write("Compliant with SS 555 / IEC 62305")
    st.write("---")
    
    # Calculate lightning protection requirements
    lp_results = engine.calculate_lightning_protection(
        building_length, building_width, building_height, 
        protection_level, roof_type
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📐 Building Parameters")
        st.write(f"- Building Dimensions: {building_length}m L x {building_width}m W x {building_height}m H")
        st.write(f"- Building Area: {lp_results['building_area']:.0f} m²")
        st.write(f"- Building Perimeter: {lp_results['perimeter']:.0f} m")
        st.write(f"- Roof Type: {roof_type}")
        st.write(f"- Protection Level: {protection_level}")
        
        st.subheader("🎯 Protection Parameters")
        st.write(f"- Protection Angle: {lp_results['protection_angle']}°")
        st.write(f"- Mesh Size: {lp_results['mesh_size']}m x {lp_results['mesh_size']}m")
        st.write(f"- Rolling Sphere Radius: {lp_results['rolling_sphere_radius']}m")
        st.write(f"- Air Terminal Spacing: {lp_results['terminal_spacing']}m")
    
    with col2:
        st.subheader("📋 Lightning Protection Bill of Materials")
        
        # Create a table with results
        lp_data = {
            "Component": [
                "Air Terminals (Lightning Rods)",
                "Down Conductors",
                "Test Joints",
                "Roof Conductor Network",
                "Down Conductor Length",
                "Total Conductor Length"
            ],
            "Quantity": [
                f"{lp_results['num_air_terminals']} nos",
                f"{lp_results['num_down_conductors']} nos",
                f"{lp_results['num_test_joints']} nos",
                f"{lp_results['roof_conductor_length']:.0f} m",
                f"{lp_results['down_conductor_length']:.0f} m",
                f"{lp_results['total_conductor_length']:.0f} m"
            ]
        }
        st.table(lp_data)
    
    # Air terminal layout visualization
    st.subheader("📍 Air Terminal Layout Recommendation")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.write("**Placement Guidelines:**")
        st.markdown(f"""
        - Install **{lp_results['num_air_terminals']}** air terminals on roof
        - Spacing: **{lp_results['terminal_spacing']}m** between terminals
        - Location: Along roof perimeter and ridges
        - Height: Minimum 0.5m above roof surface
        - Material: Copper or aluminum (minimum 16mm diameter)
        """)
    
    with col4:
        st.write("**Down Conductor Routing:**")
        st.markdown(f"""
        - Install **{lp_results['num_down_conductors']}** down conductors
        - Spacing: Maximum 20m along perimeter
        - Routing: Straightest possible path to earth
        - Protection: In PVC conduit up to 2m height
        - Bonding: Connect to main earth bar at base
        """)
    
    # Test joints
    st.subheader("🔧 Test Joint Requirements")
    st.markdown(f"""
    - Install **{lp_results['num_test_joints']}** test joints at ground level
    - Location: One per down conductor, 1.5m above ground
    - Purpose: Allows disconnection for resistance testing
    - Enclosure: Weatherproof box with clear labeling
    - Specification: Bolted link type, rated for lightning current
    """)
    
    # Special considerations
    with st.expander("📝 Special Considerations"):
        st.markdown("""
        **For Tall Buildings (>20m):**
        - Additional air terminals may be required at intermediate levels
        - Consider side flash protection on upper floors
        - Bond all metal installations within 1.5m of conductors
        
        **For Sensitive Equipment:**
        - Install Surge Protection Devices (SPDs) at main switchboard
        - Consider equipotential bonding for all services
        - Maintain separation distance from other conductors
        
        **For Structures with Roof Mounted Equipment:**
        - Protect AHUs, chillers, and other roof equipment
        - Bond equipment to lightning protection system
        - Maintain minimum 1m separation from air terminals
        """)

# --- TAB 5: EMERGENCY LIGHTING ---
with tab5:
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

# --- TAB 6: DESIGN STAGE CHECKLIST ---
with tab6:
    st.header("📋 Design Stage Checklist")
    st.write("Complete these items during the design phase")
    st.write("---")
    
    design_checklist = engine.generate_design_checklist()
    
    for category, items in design_checklist.items():
        with st.expander(f"### {category}"):
            for item in items:
                st.checkbox(item, key=f"design_{category}_{item}")

# --- TAB 7: INSTALLATION STAGE CHECKLIST ---
with tab7:
    st.header("🔧 Installation Stage Checklist")
    st.write("Complete these items during the installation phase")
    st.write("---")
    
    install_checklist = engine.generate_installation_checklist()
    
    for category, items in install_checklist.items():
        with st.expander(f"### {category}"):
            for item in items:
                st.checkbox(item, key=f"install_{category}_{item}")
    
    # Installation photos/documentation
    st.subheader("📸 Required Documentation")
    st.markdown("""
    - **Photos:** Cable routes, terminations, switchgear installation
    - **Test Reports:** Insulation resistance, earth resistance, continuity
    - **As-built Drawings:** Updated single line diagrams
    - **Equipment Manuals:** All manufacturer documentation
    - **Warranty Certificates:** For all major equipment
    - **Commissioning Reports:** Signed off by certified engineer
    """)

# --- TAB 8: MAINTENANCE & TROUBLESHOOTING ---
with tab8:
    st.header("🛠️ Maintenance Schedule & Troubleshooting Guide")
    st.write("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 Maintenance Schedule")
        maintenance = engine.generate_maintenance_checklist()
        
        for period, tasks in maintenance.items():
            with st.expander(f"### {period.upper()} Tasks"):
                for task in tasks:
                    st.checkbox(task, key=f"maint_{period}_{task}")
        
        # Maintenance log
        st.subheader("📝 Maintenance Log")
        st.text_area("Record maintenance activities, findings, and actions taken:", height=100)
        st.date_input("Next scheduled maintenance date")
    
    with col2:
        st.subheader("🔍 Troubleshooting Guide")
        troubleshooting = engine.generate_troubleshooting_guide()
        
        for category, issues in troubleshooting.items():
            with st.expander(f"### {category}"):
                for issue, steps in issues.items():
                    st.write(f"**{issue}:**")
                    for step in steps:
                        st.write(f"- {step}")
        
        # Emergency contacts
        st.subheader("📞 Emergency Contacts")
        st.markdown("""
        - **Generator Service:** [Insert Contact]
        - **Switchgear Specialist:** [Insert Contact]
        - **Fire Alarm/Pump Service:** [Insert Contact]
        - **SP Group (Emergency):** 1800 778 8888
        - **SCDF (Emergency):** 995
        """)

# --- GLOBAL DESIGN NOTES ---
st.divider()
st.subheader("💡 Project Lifecycle Summary")
col_note1, col_note2, col_note3 = st.columns(3)

with col_note1:
    st.markdown("""
    **📋 Design Phase Deliverables:**
    1. Single line diagrams
    2. Load schedules
    3. Cable schedules
    4. Equipment specifications
    5. Protection coordination study
    6. Voltage drop calculations
    7. Short circuit calculations
    8. Authority submissions
    """)

with col_note2:
    st.markdown("""
    **🔧 Installation Phase Deliverables:**
    1. Method statements
    2. Risk assessments
    3. Material test certificates
    4. Installation records
    5. Site progress photos
    6. Inspection requests
    7. Testing reports
    8. As-built drawings
    """)

with col_note3:
    st.markdown("""
    **🛠️ Maintenance Phase Requirements:**
    1. Maintenance schedule
    2. Service reports
    3. Test records
    4. Spare parts inventory
    5. Emergency procedures
    6. Training records
    7. Warranty documentation
    8. Continuous improvement log
    """)

# Footer with important notes
st.divider()
st.caption("⚠️ **Disclaimer:** This tool provides guidance based on standard practices. Always engage qualified professional engineers for final design and certification. Comply with all local regulations and authority requirements.")
