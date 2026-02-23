import streamlit as st
import math
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import hashlib
import random

# Page config must be the first Streamlit command
st.set_page_config(
    page_title="SG Electrical Design Pro", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CLASS DEFINITION ====================
class SGProEngine:
    def __init__(self):
        # Standard AT/AF Mapping
        self.standard_frames = [63, 100, 125, 160, 250, 400, 630, 800, 1000, 1250, 1600, 2000, 2500, 3200, 4000]
        self.standard_trips = [6, 10, 16, 20, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 320, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3200, 4000]
        
        # Cable Database
        self.cable_db = {
            1.5: 25, 2.5: 33, 4: 43, 6: 56, 10: 77, 16: 102, 25: 135, 35: 166, 
            50: 201, 70: 255, 95: 309, 120: 358, 150: 410, 185: 469, 240: 551, 300: 627
        }
        
        # Cable impedance (simplified)
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
            300: {"r": 0.0795, "x": 0.085}
        }
        
        # Cable diameters for tray sizing
        self.cable_diameters = {
            1.5: 12, 2.5: 13, 4: 14, 6: 15, 10: 17, 16: 19, 25: 22, 35: 24,
            50: 27, 70: 30, 95: 33, 120: 36, 150: 39, 185: 42, 240: 46, 300: 50
        }
        
        # Lighting Standards (expanded for large spaces)
        self.lighting_standards = {
            "Office": {"lux": 400, "watt_per_m2": 8, "type": "LED Panel"},
            "Meeting Room": {"lux": 500, "watt_per_m2": 12, "type": "LED Downlight"},
            "Corridor": {"lux": 150, "watt_per_m2": 5, "type": "LED Bulkhead"},
            "Car Park": {"lux": 75, "watt_per_m2": 3, "type": "LED Batten"},
            "Restaurant": {"lux": 200, "watt_per_m2": 10, "type": "LED Ambient"},
            "Kitchen": {"lux": 500, "watt_per_m2": 15, "type": "LED Vapor-tight"},
            "Warehouse": {"lux": 200, "watt_per_m2": 6, "type": "LED Highbay"},
            "Hawker Centre": {"lux": 300, "watt_per_m2": 10, "type": "LED Highbay"},
            "Market": {"lux": 300, "watt_per_m2": 10, "type": "LED Highbay"},
            "Exhibition Hall": {"lux": 300, "watt_per_m2": 12, "type": "LED Highbay"},
            "Sports Hall": {"lux": 500, "watt_per_m2": 15, "type": "LED Sports Light"},
            "Factory": {"lux": 300, "watt_per_m2": 10, "type": "LED Industrial"},
            "Plant Room": {"lux": 200, "watt_per_m2": 6, "type": "LED Batten"},
            "Toilet": {"lux": 150, "watt_per_m2": 6, "type": "LED Downlight IP44"}
        }
        
        # Socket Standards
        self.socket_standards = {
            "Office": {"density": 8, "type": "13A 2-gang", "load_per_socket": 300},
            "Meeting Room": {"density": 6, "type": "13A 2-gang + USB", "load_per_socket": 300},
            "Corridor": {"density": 20, "type": "13A 1-gang", "load_per_socket": 150},
            "Car Park": {"density": 100, "type": "13A IP66", "load_per_socket": 150},
            "Restaurant": {"density": 10, "type": "13A 2-gang", "load_per_socket": 300},
            "Kitchen": {"density": 5, "type": "13A/32A Industrial", "load_per_socket": 500},
            "Warehouse": {"density": 50, "type": "13A Heavy Duty", "load_per_socket": 300},
            "Hawker Centre": {"density": 10, "type": "13A IP66", "load_per_socket": 300},
            "Market": {"density": 10, "type": "13A IP66", "load_per_socket": 300},
            "Exhibition Hall": {"density": 20, "type": "16A Commando", "load_per_socket": 500},
            "Factory": {"density": 25, "type": "16A/32A Industrial", "load_per_socket": 500}
        }
        
        # EV Charger Config
        self.ev_config = {
            "percentage": 15,
            "power_per_charger": 7,
            "diversity": 0.6
        }
        
        # Maintenance data
        self.equipment_lifetime = {
            "LED Lighting": 50000,
            "MCB/MCCB": 20,
            "ACB": 25,
            "Cables": 30,
            "Generator": 20,
            "UPS Battery": 5,
            "Fan Motor": 10,
            "Pump Motor": 15,
            "EV Charger": 10
        }
        
        # Maintenance templates
        self.maintenance_templates = {
            "daily": ["Generator visual check", "Battery charger status", "Fuel level check"],
            "weekly": ["Generator run test", "Battery voltage check", "Emergency lighting test"],
            "monthly": ["Earth resistance test", "Circuit breaker exercise", "Thermal scan"],
            "quarterly": ["Insulation test", "Relay calibration", "Battery load test"],
            "annually": ["Full load generator test", "Oil change", "Professional inspection"]
        }
        
        # Fan database for large spaces
        self.fan_database = {
            "HVLS Fan (8ft)": {"coverage": 150, "power": 300, "airflow": 30000},
            "HVLS Fan (10ft)": {"coverage": 250, "power": 500, "airflow": 45000},
            "HVLS Fan (12ft)": {"coverage": 350, "power": 800, "airflow": 60000},
            "HVLS Fan (16ft)": {"coverage": 600, "power": 1200, "airflow": 90000},
            "HVLS Fan (20ft)": {"coverage": 900, "power": 1500, "airflow": 120000},
            "HVLS Fan (24ft)": {"coverage": 1200, "power": 2000, "airflow": 150000},
            "Industrial Pedestal": {"coverage": 100, "power": 800, "airflow": 25000},
            "Wall Mounted Fan": {"coverage": 50, "power": 300, "airflow": 10000},
            "Exhaust Fan (Large)": {"coverage": 200, "power": 250, "airflow": 2500}
        }
        
        # Ventilation requirements (ACH - Air Changes per Hour)
        self.ventilation_requirements = {
            "Office": {"ac": 6, "non_ac": 8},
            "Meeting Room": {"ac": 8, "non_ac": 12},
            "Corridor": {"ac": 2, "non_ac": 4},
            "Car Park": {"ac": 0, "non_ac": 6},
            "Restaurant": {"ac": 8, "non_ac": 15},
            "Kitchen": {"ac": 15, "non_ac": 30},
            "Warehouse": {"ac": 2, "non_ac": 4},
            "Hawker Centre": {"ac": 0, "non_ac": 12},
            "Market": {"ac": 0, "non_ac": 12},
            "Exhibition Hall": {"ac": 6, "non_ac": 10},
            "Sports Hall": {"ac": 8, "non_ac": 12},
            "Factory": {"ac": 4, "non_ac": 8},
            "Plant Room": {"ac": 10, "non_ac": 15}
        }

    # ==================== CORE CALCULATION METHODS ====================
    
    def get_breaker(self, current):
        """Get standard breaker rating"""
        at = next((x for x in self.standard_trips if x >= current), 4000)
        af = next((x for x in self.standard_frames if x >= at), 4000)
        return at, af
    
    def calculate_voltage_drop(self, cable_size, current, length, pf=0.85):
        """Calculate voltage drop for given cable"""
        if cable_size not in self.cable_impedance:
            return None, None
        
        imp = self.cable_impedance[cable_size]
        sin_phi = math.sqrt(1 - pf**2)
        vd_per_km = math.sqrt(3) * current * (imp["r"] * pf + imp["x"] * sin_phi)
        vd = vd_per_km * length / 1000
        vd_percent = (vd / 400) * 100
        return round(vd, 2), round(vd_percent, 2)
    
    def calculate_lighting(self, room_type, length, width, height):
        """Calculate lighting requirements for large spaces"""
        if room_type not in self.lighting_standards:
            return None
        
        area = length * width
        std = self.lighting_standards[room_type]
        
        # Adjust for high ceiling (more powerful fittings needed)
        if height > 6:
            multiplier = height / 3
        else:
            multiplier = 1
        
        # Typical LED fitting wattage based on room type
        if "Highbay" in std["type"] or "Industrial" in std["type"]:
            watt_per_fitting = 150
            lumens_per_fitting = 15000
        elif "Sports" in std["type"]:
            watt_per_fitting = 250
            lumens_per_fitting = 25000
        else:
            watt_per_fitting = 40
            lumens_per_fitting = 4000
        
        # Calculate number of fittings
        total_watts_needed = area * std["watt_per_m2"] * multiplier
        num_fittings = math.ceil(total_watts_needed / watt_per_fitting)
        
        # Ensure even number for layout
        if num_fittings % 2 != 0:
            num_fittings += 1
        
        # Calculate layout grid
        fittings_length = math.ceil(math.sqrt(num_fittings * (length / width)))
        fittings_width = math.ceil(num_fittings / fittings_length)
        
        return {
            "area": area,
            "num_fittings": num_fittings,
            "fittings_length": fittings_length,
            "fittings_width": fittings_width,
            "total_watts": num_fittings * watt_per_fitting,
            "watts_per_m2": (num_fittings * watt_per_fitting) / area,
            "fitting_type": std["type"],
            "lux_achieved": std["lux"],
            "mounting_height": f"{height}m"
        }
    
    def calculate_sockets(self, room_type, length, width):
        """Calculate socket requirements for large spaces"""
        if room_type not in self.socket_standards:
            return None
        
        area = length * width
        std = self.socket_standards[room_type]
        
        # Calculate number of sockets based on density
        num_sockets = max(2, math.ceil(area / std["density"]))
        
        # For very large areas, add more sockets
        if area > 1000:
            num_sockets = math.ceil(num_sockets * 1.2)
        
        # Calculate circuits (max 8 sockets per circuit for 13A, 4 for industrial)
        if "Industrial" in std["type"] or "Commando" in std["type"]:
            sockets_per_circuit = 4
        else:
            sockets_per_circuit = 8
        
        num_circuits = math.ceil(num_sockets / sockets_per_circuit)
        total_load = num_sockets * std["load_per_socket"]
        
        return {
            "num_sockets": num_sockets,
            "type": std["type"],
            "num_circuits": num_circuits,
            "total_load_watts": total_load,
            "load_per_socket": std["load_per_socket"]
        }
    
    def calculate_fans(self, room_type, length, width, height, is_aircond=False):
        """Calculate fan requirements for large spaces"""
        area = length * width
        volume = area * height
        
        # Get ventilation requirement
        vent = self.ventilation_requirements.get(room_type, 
                   self.ventilation_requirements.get("Office", {"ac": 6, "non_ac": 8}))
        
        ach = vent["ac"] if is_aircond else vent["non_ac"]
        required_cfm = volume * ach * 0.588  # Convert to CFM
        
        recommendations = []
        
        # For very large spaces (>=1000m²), use HVLS fans
        if area >= 1000:
            hvls_fans = [f for f in self.fan_database.keys() if "HVLS" in f]
            for fan_type in hvls_fans:
                fan = self.fan_database[fan_type]
                num_fans = math.ceil(area / fan["coverage"])
                if num_fans <= 12:  # Reasonable max
                    recommendations.append({
                        "type": fan_type,
                        "quantity": num_fans,
                        "power": num_fans * fan["power"],
                        "airflow": num_fans * fan["airflow"],
                        "coverage": fan["coverage"]
                    })
                    break
        
        # For medium spaces, use industrial pedestal fans
        elif area >= 200:
            fan = self.fan_database["Industrial Pedestal"]
            num_fans = math.ceil(area / fan["coverage"])
            recommendations.append({
                "type": "Industrial Pedestal Fan",
                "quantity": num_fans,
                "power": num_fans * fan["power"],
                "airflow": num_fans * fan["airflow"]
            })
        
        # For smaller spaces, use wall mounted fans
        else:
            fan = self.fan_database["Wall Mounted Fan"]
            num_fans = math.ceil(area / fan["coverage"])
            recommendations.append({
                "type": "Wall Mounted Fan",
                "quantity": num_fans,
                "power": num_fans * fan["power"],
                "airflow": num_fans * fan["airflow"]
            })
        
        # Add exhaust fans for certain room types
        if room_type in ["Kitchen", "Restaurant", "Toilet", "Plant Room"]:
            exhaust = self.fan_database["Exhaust Fan (Large)"]
            num_exhaust = math.ceil(required_cfm / exhaust["airflow"])
            recommendations.append({
                "type": "Exhaust Fan",
                "quantity": num_exhaust,
                "power": num_exhaust * exhaust["power"],
                "airflow": num_exhaust * exhaust["airflow"],
                "purpose": "Ventilation"
            })
        
        return {
            "area": area,
            "volume": volume,
            "ach_required": ach,
            "required_cfm": required_cfm,
            "recommendations": recommendations,
            "total_power": sum(r["power"] for r in recommendations)
        }
    
    def calculate_ev_chargers(self, total_lots):
        """Calculate EV charger requirements (15% of lots)"""
        num_chargers = math.ceil(total_lots * self.ev_config["percentage"] / 100)
        total_load = num_chargers * self.ev_config["power_per_charger"]
        diversified_load = total_load * self.ev_config["diversity"]
        circuits = math.ceil(num_chargers / 8)
        
        return {
            "num_chargers": num_chargers,
            "total_load_kw": total_load,
            "diversified_load_kw": diversified_load,
            "circuits": circuits,
            "power_per_charger": self.ev_config["power_per_charger"]
        }
    
    def calculate_generator(self, essential_kva, fire_kva, motor_kva):
        """Calculate generator size"""
        running_kva = essential_kva + fire_kva
        starting_kva = motor_kva * 1.2  # 20% safety
        required_kva = max(running_kva * 1.2, starting_kva)
        
        # Standard generator sizes
        std_sizes = [20, 30, 45, 60, 80, 100, 125, 150, 200, 250, 300, 400, 500, 630, 750, 800, 1000, 1250, 1500, 2000]
        recommended = next((x for x in std_sizes if x >= required_kva), required_kva)
        
        return {
            "running_kva": running_kva,
            "starting_kva": starting_kva,
            "required_kva": required_kva,
            "recommended_kva": recommended
        }
    
    def calculate_lightning(self, length, width, height):
        """Calculate lightning protection requirements"""
        area = length * width
        perimeter = 2 * (length + width)
        
        # Simplified calculation based on building dimensions
        if height < 10:
            spacing = 15
        elif height < 20:
            spacing = 12
        else:
            spacing = 10
        
        # Calculate terminals
        terminals_length = math.ceil(length / spacing) + 1
        terminals_width = math.ceil(width / spacing) + 1
        num_terminals = terminals_length * terminals_width
        
        # Down conductors (every 20m along perimeter)
        num_down = max(2, math.ceil(perimeter / 20))
        
        return {
            "area": area,
            "perimeter": perimeter,
            "num_terminals": num_terminals,
            "num_down_conductors": num_down,
            "num_test_joints": num_down,
            "terminal_spacing": spacing
        }
    
    def calculate_earth_pits(self, area, has_fuel=True, soil="Normal"):
        """Calculate earth pit requirements"""
        # Base pits
        gen_pits = 3 if soil == "Poor" else 2
        fuel_pits = 1 if has_fuel else 0
        
        # Lightning pits based on area
        if area <= 500:
            light_pits = 2
        elif area <= 2000:
            light_pits = 4
        elif area <= 5000:
            light_pits = 6
        elif area <= 10000:
            light_pits = 8
        else:
            light_pits = 10 + math.ceil((area - 10000) / 5000)
        
        total = gen_pits + fuel_pits + light_pits
        
        return {
            "generator_pits": gen_pits,
            "fuel_pits": fuel_pits,
            "lightning_pits": light_pits,
            "total": total
        }
    
    def predict_maintenance(self, equipment, hours, last_service):
        """Predict maintenance needs"""
        lifetime = self.equipment_lifetime.get(equipment, 10)
        
        if equipment in ["LED Lighting", "Cables"]:
            # Hours-based
            remaining = lifetime - hours
            if remaining < 1000:
                status = "Critical"
            elif remaining < 5000:
                status = "Warning"
            else:
                status = "Good"
            next_maint = f"After {max(0, remaining):.0f} hours"
        else:
            # Years-based
            years = (datetime.now() - last_service).days / 365
            remaining = lifetime - years
            if remaining < 1:
                status = "Critical"
            elif remaining < 3:
                status = "Warning"
            else:
                status = "Good"
            next_maint = f"Due in {max(0, remaining):.1f} years"
        
        return {
            "status": status,
            "next_maintenance": next_maint,
            "remaining": remaining
        }

# ==================== INITIALIZE ENGINE ====================
engine = SGProEngine()

# ==================== SIDEBAR ====================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/electrical.png", width=80)
    st.title("⚡ SG Electrical Pro")
    st.markdown("---")
    
    # Project Info
    st.subheader("📋 Project Info")
    project_name = st.text_input("Project Name", "My Building", key="sidebar_project")
    project_location = st.text_input("Location", "Singapore", key="sidebar_location")
    
    # User Role
    user_role = st.selectbox("User Role", 
                            ["Installer", "Engineer", "Facility Manager", "Consultant"],
                            key="sidebar_role")
    
    st.markdown("---")
    
    # Compliance Info
    st.info("✅ **Compliant with:**\n- SS 638 (Electrical)\n- SS 531 (Lighting)\n- SS 555 (Lightning)")
    
    st.markdown("---")
    
    # Donation Section
    st.markdown("### ☕ Support Development")
    st.markdown("If you find this tool useful, consider supporting:")
    
    paypal_url = "https://www.paypal.com/ncp/payment/C9S8JD4XC6F4E"
    st.markdown(f"[💰 Donate via PayPal]({paypal_url})")
    
    st.markdown("---")
    st.markdown(f"**Version:** 3.3 | **Updated:** 2024")
    st.markdown("**Supports large spaces up to 500m**")

# ==================== MAIN TABS ====================
st.title("🏗️ SG Electrical Design Professional")
st.markdown("Complete design tool for installers, engineers, and facility managers")
st.markdown("**Supports large spaces: Markets, Hawker Centres, Exhibition Halls, Factories (up to 500m)**")

# Create tabs
tab_names = [
    "🏢 Room Design",
    "🔌 Cable & Tray",
    "🚗 EV Chargers",
    "🔄 Generator",
    "⚡ Lightning",
    "⛓️ Earthing",
    "📊 MSB",
    "🛠️ Maintenance"
]

tabs = st.tabs(tab_names)

# ==================== TAB 1: ROOM DESIGN ====================
with tabs[0]:
    st.header("Room Electrical Design")
    st.markdown("Design lighting, socket outlets, and ventilation for any space (up to 500m length)")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📐 Room Parameters")
        
        # Room selection
        room_categories = list(engine.lighting_standards.keys())
        selected_room = st.selectbox("Room Type", room_categories, key="room_type_select")
        
        # Large space dimensions (up to 500m)
        col_dim1, col_dim2, col_dim3 = st.columns(3)
        with col_dim1:
            length = st.number_input("Length (m)", 1.0, 500.0, 30.0, key="room_length", step=5.0)
        with col_dim2:
            width = st.number_input("Width (m)", 1.0, 500.0, 20.0, key="room_width", step=5.0)
        with col_dim3:
            height = st.number_input("Height (m)", 2.0, 30.0, 6.0, key="room_height", step=1.0)
        
        # Calculate and display area
        area = length * width
        st.metric("Floor Area", f"{area:,.0f} m²")
        
        # AC Status
        ac_status = st.radio("Cooling Type", 
                            ["Air Conditioned", "Non-AC (Fan Only)"],
                            key="room_ac_status")
        
        # Design options
        include_lighting = st.checkbox("Include Lighting Design", True, key="inc_lighting")
        include_sockets = st.checkbox("Include Socket Outlets", True, key="inc_sockets")
        include_fans = st.checkbox("Include Ventilation Fans", True, key="inc_fans")
        
        if st.button("Calculate Room Design", type="primary", key="calc_room"):
            with col2:
                st.subheader("📊 Design Results")
                
                total_load = 0
                
                # Lighting Results
                if include_lighting:
                    st.write("### 💡 Lighting")
                    lighting = engine.calculate_lighting(selected_room, length, width, height)
                    if lighting:
                        col_l1, col_l2, col_l3 = st.columns(3)
                        col_l1.metric("Fittings", lighting['num_fittings'])
                        col_l2.metric("Load", f"{lighting['total_watts']:,.0f} W")
                        col_l3.metric("W/m²", f"{lighting['watts_per_m2']:.1f}")
                        
                        st.write(f"**Type:** {lighting['fitting_type']}")
                        st.write(f"**Layout:** {lighting['fittings_length']} × {lighting['fittings_width']} grid")
                        total_load += lighting['total_watts']
                        st.divider()
                
                # Socket Results
                if include_sockets:
                    st.write("### 🔌 Sockets")
                    sockets = engine.calculate_sockets(selected_room, length, width)
                    if sockets:
                        col_s1, col_s2, col_s3 = st.columns(3)
                        col_s1.metric("Sockets", sockets['num_sockets'])
                        col_s2.metric("Circuits", sockets['num_circuits'])
                        col_s3.metric("Load", f"{sockets['total_load_watts']:,.0f} W")
                        
                        st.write(f"**Type:** {sockets['type']}")
                        total_load += sockets['total_load_watts']
                        st.divider()
                
                # Fan Results
                if include_fans:
                    st.write("### 🌀 Ventilation Fans")
                    fans = engine.calculate_fans(selected_room, length, width, height, 
                                                "Air Conditioned" in ac_status)
                    if fans and fans['recommendations']:
                        st.metric("Required Airflow", f"{fans['required_cfm']:,.0f} CFM")
                        
                        for fan in fans['recommendations']:
                            st.write(f"**{fan['type']}:** {fan['quantity']} units")
                            st.write(f"- Power: {fan['power']}W, Airflow: {fan['airflow']:,.0f} CFM")
                            total_load += fan['power']
                        st.divider()
                
                # Total Load
                st.success(f"### 📊 Total Electrical Load: {total_load/1000:.2f} kW")
                st.info(f"**Estimated Current (230V 1-ph):** {total_load/230:.0f} A")
                if total_load/230 > 100:
                    st.warning("💡 Consider 3-phase supply for loads >100A")

# ==================== TAB 2: CABLE & TRAY ====================
with tabs[1]:
    st.header("Cable & Tray Sizing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Voltage Drop Calculator")
        
        cable_size = st.selectbox("Cable Size (mm²)", 
                                  list(engine.cable_impedance.keys()), 
                                  key="vd_cable_size")
        current = st.number_input("Load Current (A)", 1.0, 2000.0, 100.0, key="vd_current")
        distance = st.number_input("Cable Length (m)", 1.0, 1000.0, 50.0, key="vd_distance")
        pf = st.slider("Power Factor", 0.7, 1.0, 0.85, key="vd_pf")
        
        if st.button("Calculate Voltage Drop", type="primary", key="calc_vd"):
            vd, vd_pct = engine.calculate_voltage_drop(cable_size, current, distance, pf)
            
            with col2:
                st.subheader("Results")
                if vd is not None:
                    st.metric("Voltage Drop", f"{vd} V")
                    st.metric("Percentage", f"{vd_pct}%")
                    
                    if vd_pct <= 4:
                        st.success("✅ Within acceptable limit (4%)")
                    else:
                        st.error("❌ Exceeds 4% limit - use larger cable")
                        
                        # Suggest larger cable
                        larger_sizes = [s for s in engine.cable_impedance.keys() if s > cable_size]
                        if larger_sizes:
                            st.info(f"Try: {larger_sizes[0]} mm² or larger")

# ==================== TAB 3: EV CHARGERS ====================
with tabs[2]:
    st.header("🚗 EV Charger Infrastructure")
    st.markdown("Based on **15% of total carpark lots** requirement (7kW per charger)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        total_lots = st.number_input("Total Carpark Lots", 10, 5000, 200, key="ev_total_lots", step=10)
        
        st.info(f"**Requirement:** 15% of {total_lots} lots = {math.ceil(total_lots * 0.15)} chargers minimum")
        
        charger_type = st.selectbox("Charger Type",
                                   ["AC Level 2 (7kW)", "AC Fast (22kW)", "DC Fast (50kW)"],
                                   key="ev_charger_type")
        
        if st.button("Calculate EV Requirements", type="primary", key="calc_ev"):
            ev = engine.calculate_ev_chargers(total_lots)
            
            with col2:
                st.subheader("📊 EV Infrastructure Results")
                
                col_ev1, col_ev2, col_ev3 = st.columns(3)
                col_ev1.metric("EV Chargers", ev['num_chargers'])
                col_ev2.metric("Total Load", f"{ev['total_load_kw']} kW")
                col_ev3.metric("Diversified Load", f"{ev['diversified_load_kw']} kW")
                
                st.metric("Circuits Needed", ev['circuits'])
                st.metric("Power per Charger", f"{ev['power_per_charger']} kW")
                
                st.info("**📋 Installation Requirements:**")
                st.write("- Use Type B RCD for DC leakage protection")
                st.write("- Consider smart charging for load management")
                st.write(f"- Install {ev['circuits']} dedicated 3-phase circuits")
                st.write("- Each charger requires local isolator")
                
                # Load contribution
                st.success(f"**⚡ Contribution to Building Load:** {ev['diversified_load_kw']} kW")

# ==================== TAB 4: GENERATOR ====================
with tabs[3]:
    st.header("Generator Sizing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Load Inputs")
        
        essential_kva = st.number_input("Essential Loads (kVA)", 0.0, 5000.0, 100.0, key="gen_essential", step=10.0)
        fire_kva = st.number_input("Fire Fighting Loads (kVA)", 0.0, 1000.0, 30.0, key="gen_fire", step=5.0)
        motor_kva = st.number_input("Largest Motor Starting (kVA)", 0.0, 1000.0, 50.0, key="gen_motor", step=5.0)
        
        if st.button("Size Generator", type="primary", key="calc_gen"):
            gen = engine.calculate_generator(essential_kva, fire_kva, motor_kva)
            
            with col2:
                st.subheader("📊 Generator Results")
                
                col_g1, col_g2 = st.columns(2)
                col_g1.metric("Running Load", f"{gen['running_kva']:.0f} kVA")
                col_g2.metric("Starting Load", f"{gen['starting_kva']:.0f} kVA")
                
                st.metric("Required Size", f"{gen['required_kva']:.0f} kVA")
                st.success(f"### ✅ Recommended: {gen['recommended_kva']:.0f} kVA")
                
                st.info("**📋 Notes:**")
                st.write("- Includes 20% safety margin")
                st.write("- Prime rating recommended")
                st.write("- Consider future expansion")

# ==================== TAB 5: LIGHTNING ====================
with tabs[4]:
    st.header("Lightning Protection System")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Building Dimensions")
        
        bldg_length = st.number_input("Building Length (m)", 1.0, 500.0, 50.0, key="lp_length", step=5.0)
        bldg_width = st.number_input("Building Width (m)", 1.0, 500.0, 30.0, key="lp_width", step=5.0)
        bldg_height = st.number_input("Building Height (m)", 1.0, 100.0, 15.0, key="lp_height", step=2.0)
        
        if st.button("Calculate Protection", type="primary", key="calc_lp"):
            lp = engine.calculate_lightning(bldg_length, bldg_width, bldg_height)
            
            with col2:
                st.subheader("📊 Results")
                
                st.metric("Building Area", f"{lp['area']:,.0f} m²")
                st.metric("Perimeter", f"{lp['perimeter']:.0f} m")
                
                col_l1, col_l2, col_l3 = st.columns(3)
                col_l1.metric("Air Terminals", lp['num_terminals'])
                col_l2.metric("Down Conductors", lp['num_down_conductors'])
                col_l3.metric("Test Joints", lp['num_test_joints'])
                
                st.info(f"**Terminal Spacing:** {lp['terminal_spacing']}m")

# ==================== TAB 6: EARTHING ====================
with tabs[5]:
    st.header("Earthing System Design")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Parameters")
        
        bldg_area = st.number_input("Building Area (m²)", 1.0, 100000.0, 2000.0, key="earth_area", step=100.0)
        has_fuel = st.checkbox("Has Fuel Tank", True, key="earth_fuel")
        soil_type = st.selectbox("Soil Condition", ["Normal", "Poor"], key="earth_soil")
        
        if st.button("Calculate Earth Pits", type="primary", key="calc_earth"):
            pits = engine.calculate_earth_pits(bldg_area, has_fuel, soil_type)
            
            with col2:
                st.subheader("📊 Earth Pit Requirements")
                
                col_p1, col_p2, col_p3 = st.columns(3)
                col_p1.metric("Generator", pits['generator_pits'])
                col_p2.metric("Fuel Tank", pits['fuel_pits'])
                col_p3.metric("Lightning", pits['lightning_pits'])
                
                st.success(f"### Total Required: {pits['total']} earth pits")
                
                st.info("**📋 Specifications:**")
                st.write("- Depth: 3m minimum")
                st.write("- Electrode: 20mm φ copper-clad")
                st.write("- Backfill: Bentonite mix")
                st.write("- Resistance target: <1Ω combined")

# ==================== TAB 7: MSB DESIGN ====================
with tabs[6]:
    st.header("Main Switchboard Design")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Incomer Sizing")
        
        total_load_kw = st.number_input("Total Load (kW)", 10.0, 10000.0, 400.0, key="msb_load", step=50.0)
        pf = st.slider("Power Factor", 0.7, 1.0, 0.85, key="msb_pf")
        
        # Calculate current
        current = (total_load_kw * 1000) / (1.732 * 400 * pf)
        
        # Get breaker
        at, af = engine.get_breaker(current)
        
        if af >= 800:
            breaker_type = "ACB (Air Circuit Breaker)"
        elif af > 63:
            breaker_type = "MCCB (Moulded Case Circuit Breaker)"
        else:
            breaker_type = "MCB (Miniature Circuit Breaker)"
        
        with col2:
            st.subheader("📊 Results")
            
            st.metric("Design Current", f"{current:.0f} A")
            st.success(f"**Incomer:** {at}A Trip / {af}A Frame")
            st.info(f"**Type:** {breaker_type}")
            
            # Physical size estimation
            width = (800 if af >= 800 else 600) + 400 * 5  # Assuming 5 feeders
            st.metric("Est. Width", f"{width:.0f} mm")
            
            st.info("**Clearance Requirements:**")
            st.write("- Front: 1500mm")
            st.write("- Rear: 800mm")
            st.write("- Sides: 800mm")

# ==================== TAB 8: MAINTENANCE ====================
with tabs[7]:
    st.header("Maintenance Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Predictive Maintenance")
        
        equipment = st.selectbox("Equipment Type", 
                                list(engine.equipment_lifetime.keys()),
                                key="maint_equip_select")
        hours = st.slider("Operating Hours", 0, 100000, 5000, step=1000, key="maint_hours")
        last_service = st.date_input("Last Service Date", 
                                    datetime.now() - timedelta(days=180),
                                    key="maint_last_date")
        
        if st.button("Check Status", type="primary", key="check_maint"):
            pred = engine.predict_maintenance(equipment, hours, last_service)
            
            with col2:
                st.subheader("Equipment Health")
                
                # Status with color
                status_color = {"Good": "🟢", "Warning": "🟡", "Critical": "🔴"}
                st.metric("Status", f"{status_color.get(pred['status'], '⚪')} {pred['status']}")
                
                st.info(f"**Next Maintenance:** {pred['next_maintenance']}")
                
                if pred['status'] == "Critical":
                    st.error("⚠️ IMMEDIATE ACTION REQUIRED!")
                    st.write("- Schedule replacement")
                    st.write("- Order parts now")
                elif pred['status'] == "Warning":
                    st.warning("⚠️ Schedule maintenance soon")
                    st.write("- Plan for inspection")
                    st.write("- Budget for repairs")
                else:
                    st.success("✅ Equipment in good condition")
                    st.write("- Continue normal monitoring")
                    st.write("- Follow standard maintenance schedule")
    
    st.divider()
    
    # Maintenance Schedule
    st.subheader("📅 Standard Maintenance Schedule")
    
    for period, tasks in engine.maintenance_templates.items():
        with st.expander(f"**{period.upper()} Tasks**"):
            for task in tasks:
                st.checkbox(task, key=f"maint_{period}_{task}")

# ==================== FOOTER ====================
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>© SG Electrical Design Pro | Version 3.3 | Compliant with Singapore Standards</p>
    <p style='font-size: 0.8em; color: gray'>Supports large spaces up to 500m • Designed for installers, engineers, and facility managers</p>
</div>
""", unsafe_allow_html=True)
