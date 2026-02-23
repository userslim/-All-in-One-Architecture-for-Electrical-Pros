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
        
        # Cable Iz (Current Capacity) for Cu/XLPE/SWA/PVC - Table 4E4A (SS 638)
        self.cable_db = {
            1.5: 25, 2.5: 33, 4: 43, 6: 56, 10: 77, 16: 102, 25: 135, 35: 166, 
            50: 201, 70: 255, 95: 309, 120: 358, 150: 410, 185: 469, 240: 551, 300: 627,
            400: 750, 500: 860, 630: 980
        }
        
        # Cable diameter database for tray/trunking sizing
        self.cable_diameters = {
            1.5: 12, 2.5: 13, 4: 14, 6: 15, 10: 17, 16: 19, 25: 22, 35: 24,
            50: 27, 70: 30, 95: 33, 120: 36, 150: 39, 185: 42, 240: 46, 300: 50,
            400: 55, 500: 60, 630: 65
        }
        
        # Cable resistance and reactance for voltage drop
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
        
        # ==================== CABLE CONTAINMENT DATABASE ====================
        
        # Cable tray types and fill factors (based on SS 638 / IEC 61537)
        self.tray_types = {
            "Perforated Cable Tray": {
                "fill_factor": 0.4,  # 40% maximum fill
                "description": "Good ventilation, suitable for power cables",
                "typical_uses": ["General power distribution", "Mixed cable types"],
                "advantages": ["Good heat dissipation", "Light weight", "Easy cable fixing"]
            },
            "Ladder Type Tray": {
                "fill_factor": 0.4,  # 40% maximum fill
                "description": "Best for large cables, maximum ventilation",
                "typical_uses": ["Large power cables", "High current cables", "Industrial installations"],
                "advantages": ["Excellent ventilation", "Low weight", "Easy derating"]
            },
            "Solid Bottom Tray": {
                "fill_factor": 0.3,  # 30% maximum fill
                "description": "Dust protection, limited ventilation",
                "typical_uses": ["Clean rooms", "Dusty environments", "Control cables"],
                "advantages": ["Dust protection", "Neat appearance", "Cable security"]
            },
            "Wire Mesh Tray": {
                "fill_factor": 0.35,  # 35% maximum fill
                "description": "Flexible, good for data and small cables",
                "typical_uses": ["Data cables", "Control wiring", "Small power cables"],
                "advantages": ["Flexible routing", "Good visibility", "Easy modifications"]
            }
        }
        
        # Standard cable tray widths (mm)
        self.standard_tray_widths = [50, 100, 150, 200, 300, 400, 450, 500, 600, 750, 900]
        
        # Standard cable tray depths (mm)
        self.standard_tray_depths = [50, 75, 100, 150]
        
        # Cable trunking types (enclosed)
        self.trunking_types = {
            "PVC Trunking": {
                "fill_factor": 0.35,  # 35% maximum fill
                "description": "General purpose, non-metallic",
                "typical_uses": ["Lighting circuits", "Small power", "Data cables"],
                "advantages": ["Non-corrosive", "Light weight", "Easy installation"]
            },
            "Galvanized Steel Trunking": {
                "fill_factor": 0.4,  # 40% maximum fill
                "description": "Heavy duty, metallic",
                "typical_uses": ["Main feeders", "Industrial", "Fire rated installations"],
                "advantages": ["Strong", "Fire resistant", "EMC shielding"]
            },
            "Stainless Steel Trunking": {
                "fill_factor": 0.4,  # 40% maximum fill
                "description": "Corrosion resistant, hygienic",
                "typical_uses": ["Food industry", "Pharmaceutical", "Outdoor"],
                "advantages": ["Corrosion resistant", "Hygienic", "Long life"]
            }
        }
        
        # Standard trunking sizes (width × height in mm)
        self.standard_trunking_sizes = [
            {"width": 50, "height": 50},
            {"width": 75, "height": 50},
            {"width": 100, "height": 50},
            {"width": 100, "height": 75},
            {"width": 150, "height": 75},
            {"width": 150, "height": 100},
            {"width": 200, "height": 100},
            {"width": 225, "height": 100},
            {"width": 250, "height": 100},
            {"width": 300, "height": 100},
            {"width": 300, "height": 150},
            {"width": 400, "height": 150},
            {"width": 450, "height": 150},
            {"width": 500, "height": 150},
            {"width": 600, "height": 150}
        ]
        
        # Conduit types
        self.conduit_types = {
            "PVC Conduit (Light)": {
                "fill_factor": 0.4,  # 40% maximum fill
                "description": "General purpose, non-metallic",
                "typical_uses": ["Concealed wiring", "Lighting circuits", "Socket outlets"],
                "advantages": ["Corrosion resistant", "Light weight", "Low cost"]
            },
            "PVC Conduit (Heavy)": {
                "fill_factor": 0.4,  # 40% maximum fill
                "description": "Heavy duty, impact resistant",
                "typical_uses": ["Surface mounting", "Industrial", "Outdoor"],
                "advantages": ["High impact strength", "UV resistant", "Durable"]
            },
            "Galvanized Steel Conduit": {
                "fill_factor": 0.4,  # 40% maximum fill
                "description": "Metallic, high protection",
                "typical_uses": ["Industrial", "Fire rated", "EMC sensitive areas"],
                "advantages": ["Mechanical protection", "Fire resistant", "EMC shielding"]
            },
            "Flexible Conduit": {
                "fill_factor": 0.35,  # 35% maximum fill
                "description": "Flexible, for final connections",
                "typical_uses": ["Motor connections", "Vibrating equipment", "Final connections"],
                "advantages": ["Flexible", "Easy installation", "Vibration resistant"]
            }
        }
        
        # Standard conduit diameters (mm)
        self.standard_conduit_sizes = [16, 20, 25, 32, 40, 50, 63, 75, 90, 110]
        
        # Lighting Standards
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
        
        # ==================== COMPREHENSIVE FAN DATABASE ====================
        self.fan_database = {
            # HVLS Fans (High Volume Low Speed) - Large Industrial/Commercial
            "HVLS Fan - 8ft (2.4m)": {
                "type": "HVLS",
                "blade_diameter_ft": 8,
                "blade_diameter_m": 2.4,
                "coverage_m2": 150,
                "airflow_cfm": 30000,
                "power_w": 300,
                "mounting_height_min_m": 4,
                "mounting_height_ideal_m": "6-10",
                "noise_level": "Very Low",
                "speed_control": "VFD",
                "suitable_for": ["Warehouse", "Factory", "Exhibition Hall", "Sports Hall", "Hawker Centre", "Market"]
            },
            "HVLS Fan - 10ft (3.0m)": {
                "type": "HVLS",
                "blade_diameter_ft": 10,
                "blade_diameter_m": 3.0,
                "coverage_m2": 250,
                "airflow_cfm": 45000,
                "power_w": 500,
                "mounting_height_min_m": 4.5,
                "mounting_height_ideal_m": "6-12",
                "noise_level": "Very Low",
                "speed_control": "VFD",
                "suitable_for": ["Warehouse", "Factory", "Exhibition Hall", "Sports Hall", "Hawker Centre", "Market"]
            },
            "HVLS Fan - 12ft (3.7m)": {
                "type": "HVLS",
                "blade_diameter_ft": 12,
                "blade_diameter_m": 3.7,
                "coverage_m2": 350,
                "airflow_cfm": 60000,
                "power_w": 800,
                "mounting_height_min_m": 5,
                "mounting_height_ideal_m": "7-14",
                "noise_level": "Very Low",
                "speed_control": "VFD",
                "suitable_for": ["Warehouse", "Factory", "Exhibition Hall", "Sports Hall"]
            },
            "HVLS Fan - 16ft (4.9m)": {
                "type": "HVLS",
                "blade_diameter_ft": 16,
                "blade_diameter_m": 4.9,
                "coverage_m2": 600,
                "airflow_cfm": 90000,
                "power_w": 1200,
                "mounting_height_min_m": 6,
                "mounting_height_ideal_m": "8-16",
                "noise_level": "Very Low",
                "speed_control": "VFD",
                "suitable_for": ["Warehouse", "Factory", "Distribution Centre"]
            },
            "HVLS Fan - 20ft (6.1m)": {
                "type": "HVLS",
                "blade_diameter_ft": 20,
                "blade_diameter_m": 6.1,
                "coverage_m2": 900,
                "airflow_cfm": 120000,
                "power_w": 1500,
                "mounting_height_min_m": 7,
                "mounting_height_ideal_m": "9-18",
                "noise_level": "Very Low",
                "speed_control": "VFD",
                "suitable_for": ["Warehouse", "Factory", "Airport", "Convention Centre"]
            },
            "HVLS Fan - 24ft (7.3m)": {
                "type": "HVLS",
                "blade_diameter_ft": 24,
                "blade_diameter_m": 7.3,
                "coverage_m2": 1200,
                "airflow_cfm": 150000,
                "power_w": 2000,
                "mounting_height_min_m": 8,
                "mounting_height_ideal_m": "10-20",
                "noise_level": "Very Low",
                "speed_control": "VFD",
                "suitable_for": ["Very Large Warehouse", "Exhibition Hall", "Airport Hangar"]
            },
            
            # Ceiling Fans - Commercial/Industrial
            "Ceiling Fan - 48\" (1200mm) Commercial": {
                "type": "Ceiling",
                "blade_diameter_in": 48,
                "blade_diameter_mm": 1200,
                "coverage_m2": 20,
                "airflow_cfm": 6000,
                "power_w": 75,
                "mounting_height_m": "2.5-3.5",
                "noise_level": "Low",
                "speed_control": "Multi-speed",
                "suitable_for": ["Office", "Restaurant", "Shop", "Classroom"]
            },
            "Ceiling Fan - 56\" (1400mm) Commercial": {
                "type": "Ceiling",
                "blade_diameter_in": 56,
                "blade_diameter_mm": 1400,
                "coverage_m2": 25,
                "airflow_cfm": 8000,
                "power_w": 90,
                "mounting_height_m": "2.5-3.5",
                "noise_level": "Low",
                "speed_control": "Multi-speed",
                "suitable_for": ["Office", "Restaurant", "Shop", "Classroom"]
            },
            "Ceiling Fan - 60\" (1500mm) Heavy Duty": {
                "type": "Ceiling",
                "blade_diameter_in": 60,
                "blade_diameter_mm": 1500,
                "coverage_m2": 30,
                "airflow_cfm": 10000,
                "power_w": 120,
                "mounting_height_m": "3-4",
                "noise_level": "Medium",
                "speed_control": "Remote 5-speed",
                "suitable_for": ["Hawker Centre", "Market", "Gym", "Canteen"]
            },
            
            # Wall Mounted Fans
            "Wall Fan - 18\" (450mm) Oscillating": {
                "type": "Wall",
                "blade_diameter_in": 18,
                "blade_diameter_mm": 450,
                "coverage_m2": 25,
                "airflow_cfm": 4000,
                "power_w": 120,
                "mounting_height_m": "2.5-3",
                "noise_level": "Medium",
                "speed_control": "3-speed",
                "suitable_for": ["Workshop", "Kitchen", "Store", "Loading Bay"]
            },
            "Wall Fan - 24\" (600mm) Industrial": {
                "type": "Wall",
                "blade_diameter_in": 24,
                "blade_diameter_mm": 600,
                "coverage_m2": 40,
                "airflow_cfm": 7000,
                "power_w": 200,
                "mounting_height_m": "2.5-3",
                "noise_level": "Medium",
                "speed_control": "3-speed",
                "suitable_for": ["Workshop", "Factory", "Warehouse", "Loading Bay"]
            },
            "Wall Fan - 30\" (750mm) Heavy Duty": {
                "type": "Wall",
                "blade_diameter_in": 30,
                "blade_diameter_mm": 750,
                "coverage_m2": 60,
                "airflow_cfm": 10000,
                "power_w": 300,
                "mounting_height_m": "3-4",
                "noise_level": "High",
                "speed_control": "3-speed",
                "suitable_for": ["Factory", "Warehouse", "Industrial Workshop"]
            },
            
            # Pedestal Fans
            "Pedestal Fan - 18\" (450mm)": {
                "type": "Pedestal",
                "blade_diameter_in": 18,
                "blade_diameter_mm": 450,
                "coverage_m2": 20,
                "airflow_cfm": 3500,
                "power_w": 80,
                "mounting_height": "Adjustable",
                "noise_level": "Medium",
                "speed_control": "3-speed",
                "suitable_for": ["Office", "Shop", "Temporary Area"]
            },
            "Pedestal Fan - 24\" (600mm) Industrial": {
                "type": "Pedestal",
                "blade_diameter_in": 24,
                "blade_diameter_mm": 600,
                "coverage_m2": 35,
                "airflow_cfm": 6000,
                "power_w": 150,
                "mounting_height": "Adjustable",
                "noise_level": "High",
                "speed_control": "3-speed",
                "suitable_for": ["Workshop", "Factory", "Warehouse", "Event"]
            },
            
            # Exhaust Fans
            "Exhaust Fan - 10\" (250mm)": {
                "type": "Exhaust",
                "blade_diameter_in": 10,
                "blade_diameter_mm": 250,
                "airflow_cfm": 500,
                "power_w": 50,
                "noise_level": "Low",
                "suitable_for": ["Toilet", "Store Room", "Small Office"]
            },
            "Exhaust Fan - 12\" (300mm)": {
                "type": "Exhaust",
                "blade_diameter_in": 12,
                "blade_diameter_mm": 300,
                "airflow_cfm": 800,
                "power_w": 80,
                "noise_level": "Medium",
                "suitable_for": ["Toilet", "Kitchen", "Store Room"]
            },
            "Exhaust Fan - 16\" (400mm) Industrial": {
                "type": "Exhaust",
                "blade_diameter_in": 16,
                "blade_diameter_mm": 400,
                "airflow_cfm": 1500,
                "power_w": 150,
                "noise_level": "Medium",
                "suitable_for": ["Kitchen", "Plant Room", "Workshop"]
            },
            "Exhaust Fan - 20\" (500mm) Heavy Duty": {
                "type": "Exhaust",
                "blade_diameter_in": 20,
                "blade_diameter_mm": 500,
                "airflow_cfm": 2500,
                "power_w": 250,
                "noise_level": "High",
                "suitable_for": ["Commercial Kitchen", "Factory", "Plant Room"]
            },
            
            # Jet Fans (for car parks)
            "Jet Fan - 25N Thrust": {
                "type": "Jet",
                "thrust_n": 25,
                "airflow_cfm": 8000,
                "power_w": 550,
                "mounting": "Below ceiling",
                "suitable_for": ["Car Park", "Tunnel"]
            },
            "Jet Fan - 35N Thrust": {
                "type": "Jet",
                "thrust_n": 35,
                "airflow_cfm": 12000,
                "power_w": 750,
                "mounting": "Below ceiling",
                "suitable_for": ["Car Park", "Tunnel"]
            },
            "Jet Fan - 45N Thrust": {
                "type": "Jet",
                "thrust_n": 45,
                "airflow_cfm": 16000,
                "power_w": 1100,
                "mounting": "Below ceiling",
                "suitable_for": ["Large Car Park", "Tunnel"]
            }
        }
        
        # Ventilation requirements
        self.ventilation_requirements = {
            "Office": {"ac": 6, "non_ac": 8, "purpose": "Fresh air for occupants"},
            "Meeting Room": {"ac": 8, "non_ac": 12, "purpose": "Higher occupancy"},
            "Corridor": {"ac": 2, "non_ac": 4, "purpose": "Basic ventilation"},
            "Car Park": {"ac": 0, "non_ac": 6, "purpose": "CO removal, smoke control"},
            "Restaurant": {"ac": 8, "non_ac": 15, "purpose": "Odour control"},
            "Kitchen": {"ac": 15, "non_ac": 30, "purpose": "Heat and fume extraction"},
            "Toilet": {"ac": 10, "non_ac": 15, "purpose": "Odour removal"},
            "Warehouse": {"ac": 2, "non_ac": 4, "purpose": "Heat removal"},
            "Hawker Centre": {"ac": 0, "non_ac": 12, "purpose": "Heat and fume extraction"},
            "Market": {"ac": 0, "non_ac": 12, "purpose": "Ventilation"},
            "Exhibition Hall": {"ac": 6, "non_ac": 10, "purpose": "Occupant comfort"},
            "Sports Hall": {"ac": 8, "non_ac": 12, "purpose": "Active occupants"},
            "Factory": {"ac": 4, "non_ac": 8, "purpose": "Heat and fume removal"},
            "Plant Room": {"ac": 10, "non_ac": 15, "purpose": "Equipment cooling"},
            "Generator Room": {"ac": 20, "non_ac": 30, "purpose": "Combustion air + cooling"}
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
            "HVLS Fan Motor": 15,
            "Pump Motor": 15,
            "EV Charger": 10
        }
        
        # Maintenance templates
        self.maintenance_templates = {
            "daily": ["Generator visual check", "Battery charger status", "Fuel level check"],
            "weekly": ["Generator run test", "Battery voltage check", "Emergency lighting test", "Fan operation check"],
            "monthly": ["Earth resistance test", "Circuit breaker exercise", "Thermal scan", "Fan bearing check"],
            "quarterly": ["Insulation test", "Relay calibration", "Battery load test", "HVLS fan tension check"],
            "annually": ["Full load generator test", "Oil change", "Professional inspection", "Fan motor servicing"]
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
    
    # ==================== CABLE CONTAINMENT SIZING METHODS ====================
    
    def calculate_tray_size(self, cables, tray_depth=50, tray_type="Perforated Cable Tray", spare_percent=20):
        """
        Calculate required cable tray size based on cable diameters
        Includes spare capacity (default 20%)
        """
        total_area = 0
        cable_details = []
        
        for cable_size in cables:
            if cable_size in self.cable_diameters:
                diameter = self.cable_diameters[cable_size]
                radius = diameter / 2
                area = math.pi * (radius ** 2)
                total_area += area
                cable_details.append({
                    "size": cable_size,
                    "diameter": diameter,
                    "area": round(area, 0)
                })
        
        # Get fill factor for selected tray type
        fill_factor = self.tray_types[tray_type]["fill_factor"]
        
        # Apply spare capacity
        spare_multiplier = 1 + (spare_percent / 100)
        total_area_with_spare = total_area * spare_multiplier
        
        # Calculate required width
        required_width = total_area_with_spare / (tray_depth * fill_factor)
        
        # Select standard tray width
        selected_width = next((w for w in self.standard_tray_widths if w >= required_width), 
                              self.standard_tray_widths[-1])
        
        # Calculate actual fill percentages
        actual_fill = (total_area / (selected_width * tray_depth)) * 100
        actual_fill_with_spare = (total_area_with_spare / (selected_width * tray_depth)) * 100
        
        return {
            "total_cable_area": round(total_area),
            "total_area_with_spare": round(total_area_with_spare),
            "required_width": round(required_width, 1),
            "selected_width": selected_width,
            "tray_depth": tray_depth,
            "tray_type": tray_type,
            "fill_factor": fill_factor * 100,
            "actual_fill_percentage": round(actual_fill, 1),
            "actual_fill_with_spare": round(actual_fill_with_spare, 1),
            "spare_percent": spare_percent,
            "cable_details": cable_details,
            "is_adequate": actual_fill_with_spare <= (fill_factor * 100)
        }
    
    def calculate_trunking_size(self, cables, trunking_type="Galvanized Steel Trunking", spare_percent=20):
        """
        Calculate required trunking size based on cable diameters
        Includes spare capacity (default 20%)
        """
        total_area = 0
        cable_details = []
        
        for cable_size in cables:
            if cable_size in self.cable_diameters:
                diameter = self.cable_diameters[cable_size]
                radius = diameter / 2
                area = math.pi * (radius ** 2)
                total_area += area
                cable_details.append({
                    "size": cable_size,
                    "diameter": diameter,
                    "area": round(area, 0)
                })
        
        # Get fill factor for selected trunking type
        fill_factor = self.trunking_types[trunking_type]["fill_factor"]
        
        # Apply spare capacity
        spare_multiplier = 1 + (spare_percent / 100)
        total_area_with_spare = total_area * spare_multiplier
        
        # Find suitable trunking size
        suitable_sizes = []
        for size in self.standard_trunking_sizes:
            trunking_area = size["width"] * size["height"]
            available_area = trunking_area * fill_factor
            if available_area >= total_area_with_spare:
                suitable_sizes.append({
                    "width": size["width"],
                    "height": size["height"],
                    "area": trunking_area,
                    "available_area": available_area,
                    "fill_percentage": (total_area / trunking_area) * 100,
                    "fill_with_spare": (total_area_with_spare / trunking_area) * 100
                })
        
        if suitable_sizes:
            # Select smallest suitable size
            selected = min(suitable_sizes, key=lambda x: x["width"] * x["height"])
        else:
            selected = {
                "width": ">600",
                "height": ">150",
                "area": "Multiple trunking required",
                "fill_percentage": 0,
                "fill_with_spare": 0
            }
        
        return {
            "total_cable_area": round(total_area),
            "total_area_with_spare": round(total_area_with_spare),
            "fill_factor": fill_factor * 100,
            "spare_percent": spare_percent,
            "trunking_type": trunking_type,
            "selected_size": selected,
            "cable_details": cable_details,
            "suitable_sizes": suitable_sizes
        }
    
    def calculate_conduit_size(self, cables, conduit_type="PVC Conduit (Light)", spare_percent=20):
        """
        Calculate required conduit size based on cable diameters
        Includes spare capacity (default 20%)
        """
        total_area = 0
        cable_details = []
        
        for cable_size in cables:
            if cable_size in self.cable_diameters:
                diameter = self.cable_diameters[cable_size]
                radius = diameter / 2
                area = math.pi * (radius ** 2)
                total_area += area
                cable_details.append({
                    "size": cable_size,
                    "diameter": diameter,
                    "area": round(area, 0)
                })
        
        # Get fill factor for selected conduit type
        fill_factor = self.conduit_types[conduit_type]["fill_factor"]
        
        # Apply spare capacity
        spare_multiplier = 1 + (spare_percent / 100)
        total_area_with_spare = total_area * spare_multiplier
        
        # Find suitable conduit size
        suitable_sizes = []
        for diameter in self.standard_conduit_sizes:
            conduit_area = math.pi * ((diameter/2) ** 2)
            available_area = conduit_area * fill_factor
            if available_area >= total_area_with_spare:
                suitable_sizes.append({
                    "diameter": diameter,
                    "area": round(conduit_area),
                    "available_area": round(available_area),
                    "fill_percentage": (total_area / conduit_area) * 100,
                    "fill_with_spare": (total_area_with_spare / conduit_area) * 100
                })
        
        if suitable_sizes:
            # Select smallest suitable size
            selected = min(suitable_sizes, key=lambda x: x["diameter"])
        else:
            selected = {
                "diameter": ">110",
                "area": "Multiple conduits required",
                "fill_percentage": 0,
                "fill_with_spare": 0
            }
        
        return {
            "total_cable_area": round(total_area),
            "total_area_with_spare": round(total_area_with_spare),
            "fill_factor": fill_factor * 100,
            "spare_percent": spare_percent,
            "conduit_type": conduit_type,
            "selected_size": selected,
            "cable_details": cable_details,
            "suitable_sizes": suitable_sizes
        }
    
    def select_cable(self, ib, length, pf=0.85, max_vd=4):
        """Select cable based on current and voltage drop"""
        suitable = []
        for size, iz in self.cable_db.items():
            if iz >= ib * 1.25:  # 25% safety margin
                vd, vd_percent = self.calculate_voltage_drop(size, ib, length, pf)
                if vd_percent and vd_percent <= max_vd:
                    suitable.append({
                        "size": size,
                        "iz": iz,
                        "vd": vd,
                        "vd_percent": vd_percent
                    })
        
        if suitable:
            return min(suitable, key=lambda x: x["size"])
        else:
            # Find largest that meets current
            current_suitable = [{"size": s, "iz": iz} for s, iz in self.cable_db.items() if iz >= ib * 1.25]
            if current_suitable:
                largest = max(current_suitable, key=lambda x: x["size"])
                vd, vd_percent = self.calculate_voltage_drop(largest["size"], ib, length, pf)
                return {
                    "size": largest["size"],
                    "iz": largest["iz"],
                    "vd": vd,
                    "vd_percent": vd_percent,
                    "warning": f"Voltage drop ({vd_percent}%) exceeds {max_vd}%"
                }
            return {"error": "No suitable cable found"}
    
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
    
    def get_fan_recommendations(self, room_type, length, width, height, is_aircond=False, manual_selection=None):
        """
        Get fan recommendations based on room parameters
        Can either auto-recommend or use manual selection
        """
        area = length * width
        volume = area * height
        
        # Get ventilation requirement
        vent = self.ventilation_requirements.get(room_type, 
                   self.ventilation_requirements.get("Office", {"ac": 6, "non_ac": 8, "purpose": "Ventilation"}))
        
        ach = vent["ac"] if is_aircond else vent["non_ac"]
        required_cfm = volume * ach * 0.588  # Convert to CFM
        
        recommendations = []
        
        # If manual selection is provided, use that specific fan
        if manual_selection and manual_selection in self.fan_database:
            fan = self.fan_database[manual_selection]
            
            # Calculate number needed
            if "coverage_m2" in fan:
                num_fans = math.ceil(area / fan["coverage_m2"])
            elif "airflow_cfm" in fan:
                num_fans = math.ceil(required_cfm / fan["airflow_cfm"])
            else:
                num_fans = 1
            
            recommendations.append({
                "name": manual_selection,
                "type": fan["type"],
                "specifications": fan,
                "quantity": num_fans,
                "total_power": num_fans * fan["power_w"],
                "total_airflow": num_fans * fan.get("airflow_cfm", 0),
                "coverage": fan.get("coverage_m2", "N/A"),
                "mounting": fan.get("mounting_height_m", fan.get("mounting_height_ideal_m", "Standard"))
            })
            
            return {
                "area": area,
                "volume": volume,
                "ach_required": ach,
                "required_cfm": required_cfm,
                "recommendations": recommendations,
                "total_power": sum(r["total_power"] for r in recommendations),
                "is_manual": True
            }
        
        # Auto-recommendation logic based on room characteristics
        else:
            # For very large spaces (>=1000m²) with high ceiling, use HVLS fans
            if area >= 1000 and height >= 6:
                hvls_fans = {name: fan for name, fan in self.fan_database.items() 
                            if fan["type"] == "HVLS"}
                
                # Sort by coverage (largest first)
                hvls_sorted = sorted(hvls_fans.items(), 
                                    key=lambda x: x[1]["coverage_m2"], 
                                    reverse=True)
                
                for name, fan in hvls_sorted:
                    # Find a fan that can cover the area reasonably
                    if fan["coverage_m2"] >= area * 0.3:  # At least 30% coverage
                        num_fans = math.ceil(area / fan["coverage_m2"])
                        if num_fans <= 12:  # Reasonable number
                            recommendations.append({
                                "name": name,
                                "type": "HVLS",
                                "specifications": fan,
                                "quantity": num_fans,
                                "total_power": num_fans * fan["power_w"],
                                "total_airflow": num_fans * fan["airflow_cfm"],
                                "coverage": fan["coverage_m2"],
                                "mounting": f"Min {fan['mounting_height_min_m']}m"
                            })
                            break
            
            # For large spaces (200-1000m²), consider HVLS or commercial ceiling fans
            elif area >= 200:
                # Check ceiling height
                if height >= 5:
                    # Try HVLS fans
                    hvls_fans = {name: fan for name, fan in self.fan_database.items() 
                                if fan["type"] == "HVLS" and fan["coverage_m2"] <= 600}
                    
                    for name, fan in hvls_fans.items():
                        num_fans = math.ceil(area / fan["coverage_m2"])
                        if num_fans <= 6:
                            recommendations.append({
                                "name": name,
                                "type": "HVLS",
                                "specifications": fan,
                                "quantity": num_fans,
                                "total_power": num_fans * fan["power_w"],
                                "total_airflow": num_fans * fan["airflow_cfm"],
                                "coverage": fan["coverage_m2"],
                                "mounting": f"Min {fan['mounting_height_min_m']}m"
                            })
                            break
                
                # If no HVLS selected, use heavy duty ceiling fans
                if not recommendations:
                    ceiling_fans = {name: fan for name, fan in self.fan_database.items() 
                                   if fan["type"] == "Ceiling" and "Heavy Duty" in name}
                    
                    for name, fan in ceiling_fans.items():
                        num_fans = math.ceil(area / fan["coverage_m2"])
                        recommendations.append({
                            "name": name,
                            "type": "Ceiling",
                            "specifications": fan,
                            "quantity": num_fans,
                            "total_power": num_fans * fan["power_w"],
                            "total_airflow": num_fans * fan["airflow_cfm"],
                            "coverage": fan["coverage_m2"],
                            "mounting": fan["mounting_height_m"]
                        })
                        break
            
            # For medium spaces (50-200m²), use commercial ceiling fans
            elif area >= 50:
                ceiling_fans = {name: fan for name, fan in self.fan_database.items() 
                               if fan["type"] == "Ceiling" and "Commercial" in name}
                
                for name, fan in ceiling_fans.items():
                    num_fans = math.ceil(area / fan["coverage_m2"])
                    recommendations.append({
                        "name": name,
                        "type": "Ceiling",
                        "specifications": fan,
                        "quantity": num_fans,
                        "total_power": num_fans * fan["power_w"],
                        "total_airflow": num_fans * fan["airflow_cfm"],
                        "coverage": fan["coverage_m2"],
                        "mounting": fan["mounting_height_m"]
                    })
                    break
            
            # For smaller spaces, use standard ceiling fans or wall fans
            else:
                if height < 3:
                    # Use wall mounted fans
                    wall_fans = {name: fan for name, fan in self.fan_database.items() 
                                if fan["type"] == "Wall"}
                    
                    for name, fan in wall_fans.items():
                        num_fans = math.ceil(area / fan["coverage_m2"])
                        recommendations.append({
                            "name": name,
                            "type": "Wall",
                            "specifications": fan,
                            "quantity": num_fans,
                            "total_power": num_fans * fan["power_w"],
                            "total_airflow": num_fans * fan["airflow_cfm"],
                            "coverage": fan["coverage_m2"],
                            "mounting": fan["mounting_height_m"]
                        })
                        break
                else:
                    # Use ceiling fans
                    ceiling_fans = {name: fan for name, fan in self.fan_database.items() 
                                   if fan["type"] == "Ceiling"}
                    
                    for name, fan in ceiling_fans.items():
                        num_fans = math.ceil(area / fan["coverage_m2"])
                        recommendations.append({
                            "name": name,
                            "type": "Ceiling",
                            "specifications": fan,
                            "quantity": num_fans,
                            "total_power": num_fans * fan["power_w"],
                            "total_airflow": num_fans * fan["airflow_cfm"],
                            "coverage": fan["coverage_m2"],
                            "mounting": fan["mounting_height_m"]
                        })
                        break
            
            # Add exhaust fans for rooms that need ventilation
            if room_type in ["Kitchen", "Restaurant", "Toilet", "Plant Room", "Generator Room", "Car Park"]:
                exhaust_fans = {name: fan for name, fan in self.fan_database.items() 
                               if fan["type"] == "Exhaust"}
                
                # Calculate required exhaust CFM
                if room_type == "Car Park":
                    # For car parks, use jet fans
                    jet_fans = {name: fan for name, fan in self.fan_database.items() 
                               if fan["type"] == "Jet"}
                    
                    for name, fan in jet_fans.items():
                        num_fans = math.ceil(required_cfm / fan["airflow_cfm"])
                        recommendations.append({
                            "name": name,
                            "type": "Jet Fan",
                            "specifications": fan,
                            "quantity": num_fans,
                            "total_power": num_fans * fan["power_w"],
                            "total_airflow": num_fans * fan["airflow_cfm"],
                            "purpose": "Smoke control and ventilation"
                        })
                        break
                else:
                    # For other rooms, use exhaust fans
                    for name, fan in exhaust_fans.items():
                        if fan["airflow_cfm"] >= required_cfm * 0.5:  # Fan can handle at least 50%
                            num_fans = math.ceil(required_cfm / fan["airflow_cfm"])
                            if num_fans <= 4:
                                recommendations.append({
                                    "name": name,
                                    "type": "Exhaust",
                                    "specifications": fan,
                                    "quantity": num_fans,
                                    "total_power": num_fans * fan["power_w"],
                                    "total_airflow": num_fans * fan["airflow_cfm"],
                                    "purpose": "Mechanical ventilation"
                                })
                                break
        
        return {
            "area": area,
            "volume": volume,
            "ach_required": ach,
            "required_cfm": required_cfm,
            "recommendations": recommendations,
            "total_power": sum(r["total_power"] for r in recommendations),
            "purpose": vent.get("purpose", "Ventilation"),
            "is_manual": False
        }
    
    def get_fan_types_by_category(self, category=None):
        """Get fan types filtered by category"""
        if category:
            return {name: fan for name, fan in self.fan_database.items() 
                   if fan["type"] == category}
        return self.fan_database
    
    def get_fan_sizes_for_type(self, fan_type):
        """Get available sizes for a specific fan type"""
        fans = self.get_fan_types_by_category(fan_type)
        return list(fans.keys())
    
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
    st.markdown(f"**Version:** 3.5 | **Updated:** 2024")
    st.markdown("**Supports:** Large spaces, HVLS fans, Cable containment with 20% spare")

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
    st.markdown("Design lighting, socket outlets, and ventilation fans for any space (up to 500m length)")
    
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
        
        # Fan Selection Section (only shown if include_fans is True)
        if include_fans:
            st.subheader("🌀 Fan Selection")
            fan_selection_mode = st.radio("Fan Selection Mode",
                                         ["Auto-Recommend", "Manual Selection"],
                                         key="fan_mode")
            
            if fan_selection_mode == "Manual Selection":
                # Get fan types
                fan_types = ["HVLS", "Ceiling", "Wall", "Pedestal", "Exhaust", "Jet"]
                selected_fan_type = st.selectbox("Select Fan Type", fan_types, key="fan_type")
                
                # Get available fans of that type
                available_fans = engine.get_fan_sizes_for_type(selected_fan_type)
                if available_fans:
                    selected_fan = st.selectbox("Select Fan Model", available_fans, key="fan_model")
                    
                    # Show fan specifications
                    fan_specs = engine.fan_database[selected_fan]
                    with st.expander("📋 Fan Specifications"):
                        for key, value in fan_specs.items():
                            if key != "suitable_for":
                                st.write(f"**{key.replace('_', ' ').title()}:** {value}")
                        st.write("**Suitable For:**", ", ".join(fan_specs.get("suitable_for", ["General"])))
                else:
                    st.warning(f"No fans available in {selected_fan_type} category")
                    selected_fan = None
            else:
                selected_fan = None
        
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
                    
                    # Get fan recommendations
                    fan_results = engine.get_fan_recommendations(
                        selected_room, length, width, height,
                        "Air Conditioned" in ac_status,
                        selected_fan if fan_selection_mode == "Manual Selection" else None
                    )
                    
                    if fan_results:
                        st.metric("Required Airflow", f"{fan_results['required_cfm']:,.0f} CFM")
                        st.metric("Air Changes/Hour", fan_results['ach_required'])
                        
                        if fan_results['recommendations']:
                            for fan in fan_results['recommendations']:
                                with st.expander(f"**{fan['name']}**"):
                                    st.write(f"**Type:** {fan['type']}")
                                    st.write(f"**Quantity:** {fan['quantity']} units")
                                    st.write(f"**Total Power:** {fan['total_power']}W")
                                    st.write(f"**Total Airflow:** {fan['total_airflow']:,.0f} CFM")
                                    
                                    # Show key specifications
                                    specs = fan['specifications']
                                    if 'blade_diameter_ft' in specs:
                                        st.write(f"**Blade Diameter:** {specs['blade_diameter_ft']}ft ({specs['blade_diameter_m']}m)")
                                    elif 'blade_diameter_in' in specs:
                                        st.write(f"**Blade Diameter:** {specs['blade_diameter_in']}\" ({specs['blade_diameter_mm']}mm)")
                                    
                                    st.write(f"**Coverage per Fan:** {fan.get('coverage', 'N/A')} m²")
                                    st.write(f"**Mounting:** {fan['mounting']}")
                                    st.write(f"**Noise Level:** {specs.get('noise_level', 'N/A')}")
                                    st.write(f"**Speed Control:** {specs.get('speed_control', 'Standard')}")
                            
                            total_load += fan_results['total_power']
                            st.info(f"**Purpose:** {fan_results.get('purpose', 'Ventilation')}")
                        else:
                            st.warning("No fan recommendations available for this space")
                        
                        st.divider()
                
                # Total Load
                st.success(f"### 📊 Total Electrical Load: {total_load/1000:.2f} kW")
                st.info(f"**Estimated Current (230V 1-ph):** {total_load/230:.0f} A")
                if total_load/230 > 100:
                    st.warning("💡 Consider 3-phase supply for loads >100A")

# ==================== TAB 2: CABLE & TRAY (Enhanced with 20% spare) ====================
with tabs[1]:
    st.header("🔌 Cable & Containment Sizing")
    st.markdown("Calculate voltage drop and size cable trays, trunking, and conduits with **20% spare capacity**")
    
    # Create sub-tabs for different containment types
    containment_tabs = st.tabs(["Voltage Drop", "Cable Tray", "Cable Trunking", "Conduit"])
    
    # ===== VOLTAGE DROP TAB =====
    with containment_tabs[0]:
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
                    st.subheader("📊 Results")
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
    
    # ===== CABLE TRAY TAB =====
    with containment_tabs[1]:
        st.subheader("📦 Cable Tray Sizing")
        st.markdown("Calculate required tray size with **20% spare capacity** for future cables")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Cable selection
            st.write("### Select Cables in Tray")
            
            num_cable_types = st.number_input("Number of Different Cable Sizes", 1, 10, 3, key="tray_num_types")
            
            cables_in_tray = []
            cable_inputs = []
            
            for i in range(num_cable_types):
                col_c, col_q = st.columns(2)
                with col_c:
                    size = st.selectbox(f"Cable {i+1} Size (mm²)", 
                                       list(engine.cable_diameters.keys()), 
                                       key=f"tray_cable_{i}")
                with col_q:
                    qty = st.number_input(f"Quantity", 1, 100, 5, key=f"tray_qty_{i}")
                
                cable_inputs.append({"size": size, "qty": qty})
                for _ in range(qty):
                    cables_in_tray.append(size)
            
            # Tray parameters
            st.write("### Tray Parameters")
            
            tray_type = st.selectbox("Tray Type", 
                                    list(engine.tray_types.keys()), 
                                    key="tray_type_select")
            
            tray_depth = st.selectbox("Tray Depth (mm)", 
                                     engine.standard_tray_depths, 
                                     key="tray_depth_select")
            
            # Show tray type information
            with st.expander("ℹ️ Tray Type Information"):
                tray_info = engine.tray_types[tray_type]
                st.write(f"**Description:** {tray_info['description']}")
                st.write(f"**Max Fill Factor:** {tray_info['fill_factor']*100}%")
                st.write(f"**Typical Uses:** {', '.join(tray_info['typical_uses'])}")
                st.write(f"**Advantages:** {', '.join(tray_info['advantages'])}")
            
            # Spare capacity (fixed at 20% but can be adjusted)
            spare_percent = st.slider("Spare Capacity %", 0, 50, 20, key="tray_spare")
            
            if st.button("Calculate Tray Size", type="primary", key="calc_tray"):
                result = engine.calculate_tray_size(cables_in_tray, tray_depth, tray_type, spare_percent)
                
                with col2:
                    st.subheader("📊 Tray Sizing Results")
                    
                    # Summary metrics
                    col_m1, col_m2 = st.columns(2)
                    with col_m1:
                        st.metric("Total Cable Area", f"{result['total_cable_area']} mm²")
                    with col_m2:
                        st.metric("With {spare_percent}% Spare", f"{result['total_area_with_spare']} mm²")
                    
                    st.metric("Required Tray Width", f"{result['required_width']:.0f} mm")
                    
                    # Selected tray
                    st.success(f"### ✅ Selected Tray: {result['selected_width']} mm wide × {result['tray_depth']} mm deep")
                    
                    # Fill percentages
                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        st.metric("Actual Fill", f"{result['actual_fill_percentage']}%")
                    with col_f2:
                        st.metric("Fill with Spare", f"{result['actual_fill_with_spare']}%")
                    
                    # Adequacy check
                    if result['is_adequate']:
                        st.success(f"✅ Tray size is adequate (fill ≤ {result['fill_factor']}%)")
                    else:
                        st.error(f"❌ Tray is overfilled! Fill with spare ({result['actual_fill_with_spare']}%) exceeds maximum ({result['fill_factor']}%)")
                        st.info("💡 Consider:\n- Using a larger tray\n- Adding another tray\n- Reducing cables per tray")
                    
                    # Cable details
                    with st.expander("📋 Cable Details"):
                        for cable in result['cable_details']:
                            st.write(f"- {cable['size']}mm²: Ø{cable['diameter']}mm, Area {cable['area']}mm²")
    
    # ===== CABLE TRUNKING TAB =====
    with containment_tabs[2]:
        st.subheader("📦 Cable Trunking Sizing")
        st.markdown("Calculate required trunking size with **20% spare capacity** for future cables")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Cable selection
            st.write("### Select Cables in Trunking")
            
            num_cable_types_trunk = st.number_input("Number of Different Cable Sizes", 1, 10, 3, key="trunk_num_types")
            
            cables_in_trunk = []
            
            for i in range(num_cable_types_trunk):
                col_c, col_q = st.columns(2)
                with col_c:
                    size = st.selectbox(f"Cable {i+1} Size (mm²)", 
                                       list(engine.cable_diameters.keys()), 
                                       key=f"trunk_cable_{i}")
                with col_q:
                    qty = st.number_input(f"Quantity", 1, 100, 5, key=f"trunk_qty_{i}")
                
                for _ in range(qty):
                    cables_in_trunk.append(size)
            
            # Trunking parameters
            st.write("### Trunking Parameters")
            
            trunking_type = st.selectbox("Trunking Type", 
                                        list(engine.trunking_types.keys()), 
                                        key="trunking_type_select")
            
            # Show trunking type information
            with st.expander("ℹ️ Trunking Type Information"):
                trunk_info = engine.trunking_types[trunking_type]
                st.write(f"**Description:** {trunk_info['description']}")
                st.write(f"**Max Fill Factor:** {trunk_info['fill_factor']*100}%")
                st.write(f"**Typical Uses:** {', '.join(trunk_info['typical_uses'])}")
                st.write(f"**Advantages:** {', '.join(trunk_info['advantages'])}")
            
            # Spare capacity
            spare_percent_trunk = st.slider("Spare Capacity %", 0, 50, 20, key="trunk_spare")
            
            if st.button("Calculate Trunking Size", type="primary", key="calc_trunk"):
                result = engine.calculate_trunking_size(cables_in_trunk, trunking_type, spare_percent_trunk)
                
                with col2:
                    st.subheader("📊 Trunking Sizing Results")
                    
                    # Summary metrics
                    col_m1, col_m2 = st.columns(2)
                    with col_m1:
                        st.metric("Total Cable Area", f"{result['total_cable_area']} mm²")
                    with col_m2:
                        st.metric(f"With {spare_percent_trunk}% Spare", f"{result['total_area_with_spare']} mm²")
                    
                    # Selected trunking
                    if isinstance(result['selected_size']['width'], int):
                        st.success(f"### ✅ Selected Trunking: {result['selected_size']['width']} × {result['selected_size']['height']} mm")
                        st.metric("Fill Percentage", f"{result['selected_size']['fill_percentage']:.1f}%")
                        st.metric("Fill with Spare", f"{result['selected_size']['fill_with_spare']:.1f}%")
                        
                        if result['selected_size']['fill_with_spare'] <= result['fill_factor']:
                            st.success(f"✅ Trunking size is adequate (fill ≤ {result['fill_factor']}%)")
                        else:
                            st.error(f"❌ Trunking is overfilled! Fill with spare ({result['selected_size']['fill_with_spare']:.1f}%) exceeds maximum ({result['fill_factor']}%)")
                    else:
                        st.error("❌ No standard trunking size available")
                        st.info("💡 Consider:\n- Using multiple trunking runs\n- Using larger custom trunking")
                    
                    # Suitable sizes
                    if result['suitable_sizes']:
                        with st.expander("📋 Suitable Trunking Sizes"):
                            for size in result['suitable_sizes'][:5]:  # Show first 5
                                st.write(f"- {size['width']}×{size['height']}mm: Fill {size['fill_percentage']:.1f}% (with spare: {size['fill_with_spare']:.1f}%)")
    
    # ===== CONDUIT TAB =====
    with containment_tabs[3]:
        st.subheader("📦 Conduit Sizing")
        st.markdown("Calculate required conduit size with **20% spare capacity** for future cables")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Cable selection
            st.write("### Select Cables in Conduit")
            
            num_cable_types_cond = st.number_input("Number of Different Cable Sizes", 1, 10, 2, key="cond_num_types")
            
            cables_in_conduit = []
            
            for i in range(num_cable_types_cond):
                col_c, col_q = st.columns(2)
                with col_c:
                    size = st.selectbox(f"Cable {i+1} Size (mm²)", 
                                       list(engine.cable_diameters.keys()), 
                                       key=f"cond_cable_{i}")
                with col_q:
                    qty = st.number_input(f"Quantity", 1, 100, 3, key=f"cond_qty_{i}")
                
                for _ in range(qty):
                    cables_in_conduit.append(size)
            
            # Conduit parameters
            st.write("### Conduit Parameters")
            
            conduit_type = st.selectbox("Conduit Type", 
                                       list(engine.conduit_types.keys()), 
                                       key="conduit_type_select")
            
            # Show conduit type information
            with st.expander("ℹ️ Conduit Type Information"):
                cond_info = engine.conduit_types[conduit_type]
                st.write(f"**Description:** {cond_info['description']}")
                st.write(f"**Max Fill Factor:** {cond_info['fill_factor']*100}%")
                st.write(f"**Typical Uses:** {', '.join(cond_info['typical_uses'])}")
                st.write(f"**Advantages:** {', '.join(cond_info['advantages'])}")
            
            # Spare capacity
            spare_percent_cond = st.slider("Spare Capacity %", 0, 50, 20, key="cond_spare")
            
            if st.button("Calculate Conduit Size", type="primary", key="calc_cond"):
                result = engine.calculate_conduit_size(cables_in_conduit, conduit_type, spare_percent_cond)
                
                with col2:
                    st.subheader("📊 Conduit Sizing Results")
                    
                    # Summary metrics
                    col_m1, col_m2 = st.columns(2)
                    with col_m1:
                        st.metric("Total Cable Area", f"{result['total_cable_area']} mm²")
                    with col_m2:
                        st.metric(f"With {spare_percent_cond}% Spare", f"{result['total_area_with_spare']} mm²")
                    
                    # Selected conduit
                    if isinstance(result['selected_size']['diameter'], int):
                        st.success(f"### ✅ Selected Conduit: {result['selected_size']['diameter']} mm diameter")
                        st.metric("Fill Percentage", f"{result['selected_size']['fill_percentage']:.1f}%")
                        st.metric("Fill with Spare", f"{result['selected_size']['fill_with_spare']:.1f}%")
                        
                        if result['selected_size']['fill_with_spare'] <= result['fill_factor']:
                            st.success(f"✅ Conduit size is adequate (fill ≤ {result['fill_factor']}%)")
                        else:
                            st.error(f"❌ Conduit is overfilled! Fill with spare ({result['selected_size']['fill_with_spare']:.1f}%) exceeds maximum ({result['fill_factor']}%)")
                    else:
                        st.error("❌ No standard conduit size available")
                        st.info("💡 Consider:\n- Using multiple conduits\n- Using larger conduit")
                    
                    # Suitable sizes
                    if result['suitable_sizes']:
                        with st.expander("📋 Suitable Conduit Sizes"):
                            for size in result['suitable_sizes']:
                                st.write(f"- {size['diameter']}mm: Fill {size['fill_percentage']:.1f}% (with spare: {size['fill_with_spare']:.1f}%)")

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
    <p>© SG Electrical Design Pro | Version 3.5 | Compliant with Singapore Standards</p>
    <p style='font-size: 0.8em; color: gray'>Complete cable containment design: Trays, Trunking, Conduits with 20% spare capacity • HVLS Fans • EV Chargers</p>
</div>
""", unsafe_allow_html=True)
