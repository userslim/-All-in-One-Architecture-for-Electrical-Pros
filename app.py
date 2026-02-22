import streamlit as st
import math
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import hashlib
import random
import json

class SGProEngine:
    def __init__(self):
        # ==================== CORE ELECTRICAL PARAMETERS ====================
        
        # Standard AT/AF Mapping
        self.standard_frames = [63, 100, 125, 160, 250, 400, 630, 800, 1000, 1250, 1600, 2000, 2500, 3200, 4000]
        self.standard_trips = [6, 10, 16, 20, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 320, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3200, 4000]
        
        # Cable Iz (Current Capacity) for Cu/XLPE/SWA/PVC - Table 4E4A (SS 638)
        self.cable_db = {
            1.5: 25, 2.5: 33, 4: 43, 6: 56, 10: 77, 16: 102, 25: 135, 35: 166, 
            50: 201, 70: 255, 95: 309, 120: 358, 150: 410, 185: 469, 240: 551, 300: 627,
            400: 750, 500: 860, 630: 980
        }
        
        # Cable diameter database for tray sizing
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
        
        # Cable tray fill factors
        self.tray_fill_factors = {
            "perforated": 0.4,
            "ladder": 0.4,
            "solid": 0.3,
            "wire_mesh": 0.35
        }
        
        # Standard tray sizes
        self.standard_tray_sizes = [50, 100, 150, 200, 300, 400, 450, 500, 600, 750, 900]
        
        # ==================== LIGHTING STANDARDS (SS 531) ====================
        self.lighting_standards = {
            "Office (Open Plan)": {
                "recommended_lux": 400,
                "led_watt_per_m2": 8,
                "fitting_type": "LED Recessed Panel 600x600mm",
                "lumens_per_fitting": 3600,
                "watt_per_fitting": 36,
                "mounting_height": "2.8m",
                "color_temp": "4000K (Cool White)",
                "cri_requirement": ">80"
            },
            "Office (Private)": {
                "recommended_lux": 500,
                "led_watt_per_m2": 10,
                "fitting_type": "LED Recessed Panel 600x600mm",
                "lumens_per_fitting": 4000,
                "watt_per_fitting": 40,
                "mounting_height": "2.8m",
                "color_temp": "4000K (Cool White)",
                "cri_requirement": ">80"
            },
            "Meeting Room": {
                "recommended_lux": 500,
                "led_watt_per_m2": 12,
                "fitting_type": "LED Downlight / Panel (Dimmable)",
                "lumens_per_fitting": 3500,
                "watt_per_fitting": 35,
                "mounting_height": "2.6m",
                "color_temp": "3500K-4000K",
                "cri_requirement": ">90"
            },
            "Corridor / Lobby": {
                "recommended_lux": 150,
                "led_watt_per_m2": 5,
                "fitting_type": "LED Downlight / Bulkhead",
                "lumens_per_fitting": 1500,
                "watt_per_fitting": 15,
                "mounting_height": "2.8m",
                "color_temp": "4000K",
                "cri_requirement": ">80"
            },
            "Staircase": {
                "recommended_lux": 100,
                "led_watt_per_m2": 4,
                "fitting_type": "LED Wall Light / Bulkhead",
                "lumens_per_fitting": 1000,
                "watt_per_fitting": 12,
                "mounting_height": "2.5m",
                "color_temp": "4000K",
                "cri_requirement": ">80",
                "emergency_required": "100%"
            },
            "Car Park": {
                "recommended_lux": 75,
                "led_watt_per_m2": 3,
                "fitting_type": "LED Batten / Highbay",
                "lumens_per_fitting": 4000,
                "watt_per_fitting": 40,
                "mounting_height": "3-4m",
                "color_temp": "5000K (Daylight)",
                "cri_requirement": ">70"
            },
            "Retail Shop": {
                "recommended_lux": 750,
                "led_watt_per_m2": 18,
                "fitting_type": "LED Track Light / Downlight",
                "lumens_per_fitting": 3000,
                "watt_per_fitting": 30,
                "mounting_height": "3m",
                "color_temp": "3000K-3500K (Warm)",
                "cri_requirement": ">90"
            },
            "Restaurant": {
                "recommended_lux": 200,
                "led_watt_per_m2": 10,
                "fitting_type": "LED Decorative / Ambient",
                "lumens_per_fitting": 2000,
                "watt_per_fitting": 20,
                "mounting_height": "2.5m",
                "color_temp": "2700K-3000K (Warm)",
                "cri_requirement": ">90"
            },
            "Kitchen (Commercial)": {
                "recommended_lux": 500,
                "led_watt_per_m2": 15,
                "fitting_type": "LED Vapor-tight / Batten",
                "lumens_per_fitting": 4000,
                "watt_per_fitting": 40,
                "mounting_height": "3m",
                "color_temp": "4000K",
                "cri_requirement": ">80",
                "ip_rating": "IP65"
            },
            "Warehouse / Store": {
                "recommended_lux": 200,
                "led_watt_per_m2": 6,
                "fitting_type": "LED Highbay",
                "lumens_per_fitting": 15000,
                "watt_per_fitting": 150,
                "mounting_height": "6-10m",
                "color_temp": "5000K",
                "cri_requirement": ">70"
            },
            "Classroom": {
                "recommended_lux": 500,
                "led_watt_per_m2": 12,
                "fitting_type": "LED Panel / Troffer",
                "lumens_per_fitting": 4000,
                "watt_per_fitting": 40,
                "mounting_height": "2.8m",
                "color_temp": "4000K",
                "cri_requirement": ">80"
            },
            "Toilet / Bathroom": {
                "recommended_lux": 150,
                "led_watt_per_m2": 6,
                "fitting_type": "LED Downlight (IP44)",
                "lumens_per_fitting": 1200,
                "watt_per_fitting": 12,
                "mounting_height": "2.5m",
                "color_temp": "4000K",
                "cri_requirement": ">80",
                "ip_rating": "IP44"
            },
            "Plant Room": {
                "recommended_lux": 200,
                "led_watt_per_m2": 6,
                "fitting_type": "LED Batten / Vapor-tight",
                "lumens_per_fitting": 3000,
                "watt_per_fitting": 30,
                "mounting_height": "3m",
                "color_temp": "4000K",
                "cri_requirement": ">70"
            },
            "Hawker Centre": {
                "recommended_lux": 300,
                "led_watt_per_m2": 10,
                "fitting_type": "LED Highbay / Vapor-tight",
                "lumens_per_fitting": 10000,
                "watt_per_fitting": 100,
                "mounting_height": "4-6m",
                "color_temp": "4000K",
                "cri_requirement": ">80",
                "ip_rating": "IP65"
            }
        }
        
        # ==================== SOCKET OUTLET STANDARDS ====================
        self.socket_outlet_standards = {
            "Office (Open Plan)": {
                "density": "1 double socket per 5-8 m²",
                "spacing": "Along walls every 2.5-3m",
                "type": "13A BS 1363, 2-gang",
                "circuit_rating": "20A per ring circuit",
                "max_sockets_per_circuit": 8,
                "special_requirements": ["USB sockets at workstations", "Floor boxes in open areas"]
            },
            "Office (Private)": {
                "density": "4-6 double sockets per room",
                "spacing": "Each wall with sockets",
                "type": "13A BS 1363, 2-gang",
                "circuit_rating": "20A ring circuit",
                "max_sockets_per_circuit": 8,
                "special_requirements": ["Data sockets adjacent", "USB charging points"]
            },
            "Meeting Room": {
                "density": "2 double sockets per wall",
                "spacing": "Conference table with floor boxes",
                "type": "13A BS 1363, 2-gang + USB",
                "circuit_rating": "20A ring circuit",
                "max_sockets_per_circuit": 6,
                "special_requirements": ["Floor boxes for AV", "Retractable socket modules"]
            },
            "Corridor": {
                "density": "1 double socket per 15-20m",
                "spacing": "For cleaning equipment",
                "type": "13A BS 1363, 1-gang",
                "circuit_rating": "20A radial",
                "max_sockets_per_circuit": 6,
                "special_requirements": ["Maintenance access"]
            },
            "Car Park": {
                "density": "1 socket per 100m²",
                "spacing": "For maintenance equipment",
                "type": "13A BS 1363, IP66 weatherproof",
                "circuit_rating": "20A radial",
                "max_sockets_per_circuit": 4,
                "special_requirements": ["Weatherproof covers", "RCBO protection"]
            },
            "Retail Shop": {
                "density": "1 double socket per 10m²",
                "spacing": "Along display walls",
                "type": "13A BS 1363, 2-gang",
                "circuit_rating": "20A ring circuit",
                "max_sockets_per_circuit": 8,
                "special_requirements": ["POS counter sockets", "Display lighting points"]
            },
            "Restaurant": {
                "density": "1 double socket per table area",
                "spacing": "At service areas",
                "type": "13A BS 1363, 2-gang",
                "circuit_rating": "20A ring circuit",
                "max_sockets_per_circuit": 8,
                "special_requirements": ["Kitchen equipment sockets", "POS system points"]
            },
            "Kitchen (Commercial)": {
                "density": "As per equipment schedule",
                "spacing": "Individual circuits for equipment",
                "type": "13A / 32A / Industrial sockets",
                "circuit_rating": "Individual circuits",
                "max_sockets_per_circuit": 1,
                "special_requirements": ["IP66 rating near water", "RCBO per circuit", "Equipment isolation"]
            },
            "Toilet / Bathroom": {
                "density": "1 shaver socket per 2 toilets",
                "spacing": "Near mirror area",
                "type": "Shaver socket (BS 4573) / 13A",
                "circuit_rating": "20A radial with RCD",
                "max_sockets_per_circuit": 3,
                "special_requirements": ["RCD protection", "IP44 rating", "Isolation transformer for shavers"]
            },
            "Hawker Centre": {
                "density": "1 socket per stall (minimum 2)",
                "spacing": "At each stall location",
                "type": "13A BS 1363, IP66 weatherproof",
                "circuit_rating": "20A radial per stall",
                "max_sockets_per_circuit": 2,
                "special_requirements": ["Weatherproof covers", "Individual RCBO", "High temperature rating"]
            }
        }
        
        # ==================== ISOLATOR REQUIREMENTS ====================
        self.isolator_requirements = {
            "General Lighting": {
                "required": True,
                "type": "Switch (local)",
                "location": "At entrance of room",
                "purpose": "Local isolation for maintenance"
            },
            "Socket Outlets": {
                "required": True,
                "type": "MCB in DB",
                "location": "Distribution board",
                "purpose": "Circuit protection and isolation"
            },
            "Air Conditioner (Split)": {
                "required": True,
                "type": "45A Isolator with switch",
                "location": "Near unit, accessible",
                "purpose": "Local isolation for servicing"
            },
            "Kitchen Equipment": {
                "required": True,
                "type": "32A/63A Isolator with switch",
                "location": "Adjacent to equipment",
                "purpose": "Emergency isolation"
            },
            "Water Heater": {
                "required": True,
                "type": "20A Double pole isolator",
                "location": "Adjacent to heater",
                "purpose": "Local isolation for safety"
            },
            "Pump / Motor": {
                "required": True,
                "type": "Local isolator with lockable handle",
                "location": "Near pump, visible",
                "purpose": "Lockout/tagout for maintenance"
            },
            "Generator": {
                "required": True,
                "type": "ACB / MCCB with isolation",
                "location": "At generator panel",
                "purpose": "Complete isolation"
            },
            "Stall (Hawker Centre)": {
                "required": True,
                "type": "63A Isolator with switch, lockable",
                "location": "At each stall, accessible",
                "purpose": "Complete stall isolation"
            },
            "EV Charger": {
                "required": True,
                "type": "40A/63A DP Isolator with switch",
                "location": "Adjacent to charger",
                "purpose": "Local isolation for safety"
            }
        }
        
        # ==================== FAN DATABASE ====================
        self.fan_database = {
            "Ceiling Fan (Residential)": {
                "suitable_for": ["Office", "Classroom", "Restaurant", "Shop"],
                "blade_diameter": ["48\" (1200mm)", "56\" (1400mm)"],
                "coverage_area_m2": 20,
                "airflow_cfm": 6000,
                "power_watts": 75,
                "mounting_height": "2.5-3m",
                "noise_level": "Low",
                "speed_control": "Multi-speed regulator"
            },
            "Ceiling Fan (Commercial)": {
                "suitable_for": ["Hawker Centre", "Market", "Gym", "Warehouse"],
                "blade_diameter": ["56\" (1400mm)", "60\" (1500mm)"],
                "coverage_area_m2": 30,
                "airflow_cfm": 10000,
                "power_watts": 120,
                "mounting_height": "3-4m",
                "noise_level": "Medium",
                "speed_control": "Remote / 5-speed"
            },
            "High Volume Low Speed (HVLS)": {
                "suitable_for": ["Hawker Centre", "Warehouse", "Factory", "Sports Hall"],
                "blade_diameter": ["8ft (2.4m)", "10ft (3.0m)", "12ft (3.7m)", "16ft (4.9m)", "20ft (6.1m)"],
                "coverage_area_m2": {
                    "8ft": 150,
                    "10ft": 250,
                    "12ft": 350,
                    "16ft": 600,
                    "20ft": 900
                },
                "airflow_cfm": {
                    "8ft": 30000,
                    "10ft": 45000,
                    "12ft": 60000,
                    "16ft": 90000,
                    "20ft": 120000
                },
                "power_watts": {
                    "8ft": 300,
                    "10ft": 500,
                    "12ft": 800,
                    "16ft": 1200,
                    "20ft": 1500
                },
                "mounting_height": "Minimum 4m, ideal 6-10m",
                "noise_level": "Very Low",
                "speed_control": "VFD (Variable Frequency Drive)"
            },
            "Wall Mounted Fan (Oscillating)": {
                "suitable_for": ["Workshop", "Kitchen", "Store", "Loading Bay"],
                "blade_diameter": ["18\" (450mm)", "24\" (600mm)", "30\" (750mm)"],
                "coverage_area_m2": {
                    "18\"": 25,
                    "24\"": 40,
                    "30\"": 60
                },
                "airflow_cfm": {
                    "18\"": 4000,
                    "24\"": 7000,
                    "30\"": 10000
                },
                "power_watts": {
                    "18\"": 120,
                    "24\"": 200,
                    "30\"": 300
                },
                "mounting_height": "2.5-3m",
                "noise_level": "Medium",
                "speed_control": "3-speed pull cord/switch"
            },
            "Exhaust Fan (Wall/Ceiling)": {
                "suitable_for": ["Toilet", "Kitchen", "Store Room", "Plant Room"],
                "blade_diameter": ["6\" (150mm)", "8\" (200mm)", "10\" (250mm)", "12\" (300mm)"],
                "airflow_cfm": {
                    "6\"": 150,
                    "8\"": 300,
                    "10\"": 500,
                    "12\"": 800
                },
                "power_watts": {
                    "6\"": 20,
                    "8\"": 35,
                    "10\"": 50,
                    "12\"": 80
                },
                "sound_level_db": 45,
                "purpose": "Ventilation",
                "installation": "Through wall/ceiling"
            }
        }
        
        # ==================== VENTILATION REQUIREMENTS ====================
        self.ventilation_requirements = {
            "Office": {"ac_ach": 6, "non_ac_ach": 8, "notes": "Fresh air requirement 10 L/s/person"},
            "Meeting Room": {"ac_ach": 8, "non_ac_ach": 12, "notes": "Higher occupancy"},
            "Corridor": {"ac_ach": 2, "non_ac_ach": 4, "notes": "Natural ventilation if possible"},
            "Staircase": {"ac_ach": 2, "non_ac_ach": 4, "notes": "Pressurization for fire safety"},
            "Car Park": {"ac_ach": 0, "non_ac_ach": 6, "notes": "CO monitoring required"},
            "Restaurant": {"ac_ach": 8, "non_ac_ach": 15, "notes": "Kitchen separate exhaust"},
            "Kitchen": {"ac_ach": 15, "non_ac_ach": 30, "notes": "Kitchen hood required"},
            "Toilet": {"ac_ach": 10, "non_ac_ach": 15, "notes": "Mechanical exhaust mandatory"},
            "Warehouse": {"ac_ach": 2, "non_ac_ach": 4, "notes": "Ventilation for heat removal"},
            "Hawker Centre": {"ac_ach": 0, "non_ac_ach": 12, "notes": "High ceiling, mechanical extraction"},
            "Plant Room": {"ac_ach": 10, "non_ac_ach": 15, "notes": "Heat removal for equipment"},
            "Generator Room": {"ac_ach": 20, "non_ac_ach": 30, "notes": "Combustion air + cooling"}
        }
        
        # ==================== MOTOR STARTING MULTIPLIERS ====================
        self.motor_starting_multipliers = {
            "Lift (Variable Speed)": 2.5,
            "Lift (Star-Delta)": 3.0,
            "Fire Pump (Direct Online)": 6.0,
            "Fire Pump (Star-Delta)": 3.5,
            "Fire Pump (Soft Starter)": 2.5,
            "HVAC Chiller": 2.0,
            "Pressurization Fan": 3.0,
            "Water Pump": 4.0
        }
        
        # ==================== LIGHTNING PROTECTION STANDARDS ====================
        self.lightning_protection_levels = {
            "Level I": {"protection_angle": 20, "mesh_size": 5, "rolling_sphere": 20, "risk_level": "Very High"},
            "Level II": {"protection_angle": 25, "mesh_size": 10, "rolling_sphere": 30, "risk_level": "High"},
            "Level III": {"protection_angle": 35, "mesh_size": 15, "rolling_sphere": 45, "risk_level": "Normal"},
            "Level IV": {"protection_angle": 45, "mesh_size": 20, "rolling_sphere": 60, "risk_level": "Low"}
        }
        
        # Air terminal spacing
        self.air_terminal_spacing = {
            "Level I": {"low": 5, "medium": 4, "high": 3},
            "Level II": {"low": 8, "medium": 6, "high": 4},
            "Level III": {"low": 10, "medium": 8, "high": 5},
            "Level IV": {"low": 12, "medium": 10, "high": 6}
        }
        
        # ==================== MAINTENANCE & LIFETIME DATA ====================
        self.equipment_lifetime = {
            "LED Lighting": 50000,  # hours
            "MCB/MCCB": 20,  # years
            "ACB": 25,  # years
            "Cables": 30,  # years
            "Generator": 20,  # years
            "UPS Battery": 5,  # years
            "Fan Motor": 10,  # years
            "Pump Motor": 15,  # years
            "Earth Electrode": 15,  # years
            "Lightning Arrester": 10  # years
        }
        
        self.maintenance_templates = {
            "daily": [
                {"task": "Generator visual check", "duration_min": 15, "criticality": "High"},
                {"task": "Battery charger status", "duration_min": 5, "criticality": "Medium"},
                {"task": "Fuel level check", "duration_min": 5, "criticality": "High"}
            ],
            "weekly": [
                {"task": "Generator run test (30 mins)", "duration_min": 45, "criticality": "High"},
                {"task": "Battery voltage measurement", "duration_min": 15, "criticality": "Medium"},
                {"task": "Emergency lighting test", "duration_min": 20, "criticality": "High"}
            ],
            "monthly": [
                {"task": "Earth resistance measurement", "duration_min": 60, "criticality": "High"},
                {"task": "Circuit breaker exercise", "duration_min": 45, "criticality": "Medium"},
                {"task": "Thermal imaging scan", "duration_min": 90, "criticality": "High"}
            ],
            "quarterly": [
                {"task": "Insulation resistance test", "duration_min": 180, "criticality": "High"},
                {"task": "Protection relay calibration", "duration_min": 240, "criticality": "High"},
                {"task": "Battery load test", "duration_min": 60, "criticality": "High"}
            ],
            "annually": [
                {"task": "Full load generator test", "duration_min": 240, "criticality": "High"},
                {"task": "Oil and filter change", "duration_min": 120, "criticality": "High"},
                {"task": "Professional inspection", "duration_min": 480, "criticality": "High"}
            ]
        }
        
        # ==================== ENERGY TARIFFS ====================
        self.energy_tariffs = {
            "peak": {"time": "9am-12pm, 6pm-8pm", "rate": 0.30},
            "off_peak": {"time": "10pm-7am", "rate": 0.15},
            "normal": {"time": "Others", "rate": 0.22}
        }

    # ==================== CORE CALCULATION METHODS ====================
    
    def get_at_af(self, ib):
        """Select standard breaker rating based on current"""
        at = next((x for x in self.standard_trips if x >= ib), 4000)
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

    # ==================== ROOM DESIGN METHODS ====================
    
    def calculate_lighting(self, room_type, length, width, height):
        """Calculate lighting requirements for a room"""
        if room_type not in self.lighting_standards:
            return None
        
        area = length * width
        std = self.lighting_standards[room_type]
        
        # Lumen method calculation
        utilization_factor = 0.7
        maintenance_factor = 0.8
        total_lumens = (area * std["recommended_lux"]) / (utilization_factor * maintenance_factor)
        
        num_fittings = math.ceil(total_lumens / std["lumens_per_fitting"])
        if num_fittings % 2 != 0:
            num_fittings += 1
        
        # Layout calculation
        fittings_length = math.ceil(math.sqrt(num_fittings * (length / width)))
        fittings_width = math.ceil(num_fittings / fittings_length)
        
        return {
            "area": area,
            "num_fittings": num_fittings,
            "fittings_length": fittings_length,
            "fittings_width": fittings_width,
            "total_watts": num_fittings * std["watt_per_fitting"],
            "watts_per_m2": (num_fittings * std["watt_per_fitting"]) / area,
            "fitting_type": std["fitting_type"],
            "lux_achieved": (num_fittings * std["lumens_per_fitting"] * utilization_factor * maintenance_factor) / area,
            "color_temp": std["color_temp"],
            "mounting_height": std["mounting_height"]
        }
    
    def calculate_sockets(self, room_type, length, width):
        """Calculate socket outlet requirements"""
        if room_type not in self.socket_outlet_standards:
            return None
        
        area = length * width
        std = self.socket_outlet_standards[room_type]
        
        # Parse density
        if "per" in std["density"]:
            parts = std["density"].split("per")
            range_str = parts[1].strip().replace("m²", "").strip()
            if "-" in range_str:
                low, high = map(float, range_str.split("-"))
                avg_density = (low + high) / 2
            else:
                avg_density = float(range_str)
            num_sockets = math.ceil(area / avg_density)
        else:
            num_sockets = 6
        
        # Calculate circuits
        num_circuits = math.ceil(num_sockets / std["max_sockets_per_circuit"])
        total_load = num_sockets * 300  # 300W per socket
        current = total_load / (230 * 3)  # Balanced across 3 phases
        
        return {
            "num_sockets": num_sockets,
            "socket_type": std["type"],
            "num_circuits": num_circuits,
            "total_load_watts": total_load,
            "current_per_phase": round(current, 1),
            "special_requirements": std["special_requirements"]
        }
    
    def get_isolators(self, room_type, equipment_list):
        """Get isolator requirements for room"""
        isolators = []
        
        if "lighting" in equipment_list:
            isolators.append({
                "equipment": "General Lighting",
                "type": "Light switch (local)",
                "location": "At room entrance"
            })
        
        if "sockets" in equipment_list:
            isolators.append({
                "equipment": "Socket Outlets",
                "type": "MCB in DB",
                "location": "Distribution board"
            })
        
        # Room-specific isolators
        room_map = {
            "Kitchen (Commercial)": ["Kitchen Equipment"],
            "Restaurant": ["Kitchen Equipment"],
            "Toilet / Bathroom": ["Water Heater"],
            "Plant Room": ["Pump / Motor"],
            "Hawker Centre": ["Stall (Hawker Centre)"]
        }
        
        if room_type in room_map:
            for equip in room_map[room_type]:
                if equip in self.isolator_requirements:
                    isolators.append({
                        "equipment": equip,
                        "type": self.isolator_requirements[equip]["type"],
                        "location": self.isolator_requirements[equip]["location"]
                    })
        
        return isolators
    
    def calculate_fans(self, room_type, length, width, height, is_aircond=True):
        """Calculate fan requirements"""
        area = length * width
        volume = area * height
        
        # Get ventilation requirements
        vent = self.ventilation_requirements.get(room_type, 
              self.ventilation_requirements.get("Office", {"ac_ach": 6, "non_ac_ach": 8, "notes": ""}))
        
        ach = vent["ac_ach"] if is_aircond else vent["non_ac_ach"]
        required_cfm = volume * ach * 0.588
        
        recommendations = []
        
        # HVLS for large spaces
        if height >= 4 and area >= 150:
            hvls = self.fan_database["High Volume Low Speed (HVLS)"]
            for size in ["8ft", "10ft", "12ft"]:
                if hvls["coverage_area_m2"][size] >= area:
                    num = math.ceil(area / hvls["coverage_area_m2"][size])
                    recommendations.append({
                        "type": "HVLS Fan",
                        "size": size,
                        "quantity": num,
                        "power": num * hvls["power_watts"][size],
                        "airflow": num * hvls["airflow_cfm"][size],
                        "mounting": hvls["mounting_height"]
                    })
                    break
        
        # Ceiling fans for smaller spaces
        elif height <= 4:
            fan_type = "Ceiling Fan (Commercial)" if area > 100 else "Ceiling Fan (Residential)"
            fan = self.fan_database[fan_type]
            num = math.ceil(area / fan["coverage_area_m2"])
            recommendations.append({
                "type": fan_type,
                "quantity": num,
                "power": num * fan["power_watts"],
                "airflow": num * fan["airflow_cfm"],
                "mounting": fan["mounting_height"]
            })
        
        # Exhaust fans for certain rooms
        if room_type in ["Toilet / Bathroom", "Kitchen (Commercial)", "Plant Room"]:
            exhaust = self.fan_database["Exhaust Fan (Wall/Ceiling)"]
            num = math.ceil(required_cfm / 800)  # Using largest exhaust fan CFM
            recommendations.append({
                "type": "Exhaust Fan",
                "quantity": num,
                "power": num * 80,  # 80W per fan
                "airflow": num * 800,
                "purpose": "Mechanical ventilation"
            })
        
        return {
            "area": area,
            "volume": volume,
            "ach_required": ach,
            "required_cfm": required_cfm,
            "recommendations": recommendations,
            "total_power": sum(r["power"] for r in recommendations)
        }
    
    # ==================== GENERATOR SIZING ====================
    
    def calculate_generator(self, essential_loads, fire_loads, motor_starting_kva):
        """Calculate generator size"""
        running_kva = sum(essential_loads) + sum(fire_loads)
        other_running = running_kva - motor_starting_kva
        starting_kva = other_running + motor_starting_kva
        
        required = max(running_kva, starting_kva) * 1.2  # 20% safety
        
        # Standard sizes
        std_sizes = [20, 30, 45, 60, 80, 100, 125, 150, 200, 250, 300, 400, 500, 630]
        recommended = next((x for x in std_sizes if x >= required), required)
        
        return {
            "required_kva": round(required, 1),
            "recommended_kva": recommended,
            "running_kva": round(running_kva, 1),
            "starting_kva": round(starting_kva, 1)
        }
    
    # ==================== LIGHTNING PROTECTION ====================
    
    def calculate_lightning(self, length, width, height, level="Level III", roof="Flat"):
        """Calculate lightning protection requirements"""
        area = length * width
        perimeter = 2 * (length + width)
        
        spacing = self.air_terminal_spacing[level]
        if height < 10:
            term_spacing = spacing["low"]
        elif height < 20:
            term_spacing = spacing["medium"]
        else:
            term_spacing = spacing["high"]
        
        # Calculate terminals
        term_length = math.ceil(length / term_spacing) + 1
        term_width = math.ceil(width / term_spacing) + 1
        
        if roof == "Flat":
            num_terminals = term_length * term_width
        else:
            num_terminals = term_length * 2 + term_width
        
        # Down conductors (every 20m)
        num_down = max(2, math.ceil(perimeter / 20))
        
        return {
            "area": area,
            "perimeter": perimeter,
            "num_terminals": num_terminals,
            "num_down_conductors": num_down,
            "num_test_joints": num_down,
            "terminal_spacing": term_spacing,
            "protection_params": self.lightning_protection_levels[level]
        }
    
    # ==================== CABLE TRAY SIZING ====================
    
    def calculate_tray(self, cables, tray_depth=50, tray_type="perforated", spare=0.25):
        """Calculate cable tray size"""
        total_area = 0
        cable_details = []
        
        for cable_size in cables:
            if cable_size in self.cable_diameters:
                diameter = self.cable_diameters[cable_size]
                area = math.pi * (diameter/2)**2
                total_area += area
                cable_details.append({
                    "size": cable_size,
                    "diameter": diameter,
                    "area": round(area, 0)
                })
        
        # Apply spare and fill factor
        total_with_spare = total_area * (1 + spare)
        fill_factor = self.tray_fill_factors.get(tray_type, 0.4)
        required_width = total_with_spare / (tray_depth * fill_factor)
        
        # Select standard size
        selected = next((w for w in self.standard_tray_sizes if w >= required_width), 
                       self.standard_tray_sizes[-1])
        
        actual_fill = (total_area / (selected * tray_depth)) * 100
        
        return {
            "total_area": round(total_area),
            "required_width": round(required_width, 1),
            "selected_width": selected,
            "actual_fill": round(actual_fill, 1),
            "fill_factor": fill_factor * 100,
            "cable_details": cable_details
        }
    
    # ==================== EARTHING DESIGN ====================
    
    def calculate_earth_pits(self, building_area, has_fuel=True, soil="Normal", level="Level III"):
        """Calculate earth pit requirements"""
        pits = {
            "generator": 2,
            "fuel_tank": 1 if has_fuel else 0,
            "lightning": 0
        }
        
        if soil == "Poor":
            pits["generator"] = 3
        
        # Lightning pits based on area
        if building_area <= 500:
            pits["lightning"] = 2
        elif building_area <= 2000:
            pits["lightning"] = 4
        elif building_area <= 5000:
            pits["lightning"] = 6
        else:
            pits["lightning"] = 8 + math.ceil((building_area - 5000) / 2000)
        
        # Apply protection level multiplier
        multiplier = {"Level I": 1.5, "Level II": 1.2, "Level III": 1.0, "Level IV": 0.8}
        pits["lightning"] = math.ceil(pits["lightning"] * multiplier[level])
        
        pits["total"] = sum(pits.values())
        return pits
    
    # ==================== MAINTENANCE & PREDICTIVE ====================
    
    def predict_maintenance(self, equipment, hours_used, last_service):
        """Predict maintenance needs"""
        lifetime = self.equipment_lifetime.get(equipment, 10)
        
        if isinstance(lifetime, int) and lifetime > 100:  # Hours-based
            remaining = lifetime - hours_used
            if remaining < 1000:
                status = "Critical"
            elif remaining < 5000:
                status = "Warning"
            else:
                status = "Good"
            next_maint = f"After {remaining} hours"
        else:  # Years-based
            years = (datetime.now() - last_service).days / 365
            remaining = lifetime - years
            if remaining < 1:
                status = "Critical"
            elif remaining < 3:
                status = "Warning"
            else:
                status = "Good"
            next_maint = f"Due in {remaining:.1f} years"
        
        return {
            "equipment": equipment,
            "status": status,
            "next_maintenance": next_maint,
            "recommendations": self._get_recommendations(equipment, status)
        }
    
    def _get_recommendations(self, equipment, status):
        """Get maintenance recommendations"""
        base = {
            "LED Lighting": ["Clean fixtures", "Check for flickering", "Verify lux levels"],
            "MCB/MCCB": ["Exercise breakers", "Thermal imaging", "Check for tripping"],
            "Generator": ["Change oil", "Check coolant", "Test under load"],
            "UPS Battery": ["Load test", "Check electrolyte", "Clean terminals"]
        }
        
        recs = base.get(equipment, ["General inspection"])
        
        if status == "Critical":
            recs.append("IMMEDIATE ACTION REQUIRED")
            recs.append("Order replacement parts")
        elif status == "Warning":
            recs.append("Schedule maintenance soon")
        
        return recs
    
    def generate_schedule(self, equipment_list, start_date):
        """Generate maintenance schedule"""
        schedule = []
        current = datetime.strptime(start_date, "%Y-%m-%d")
        
        for eq in equipment_list:
            for period, tasks in self.maintenance_templates.items():
                for task in tasks:
                    if period == "daily":
                        due = current
                    elif period == "weekly":
                        due = current + timedelta(days=7 - current.weekday())
                    elif period == "monthly":
                        due = current.replace(day=1) + timedelta(days=32)
                        due = due.replace(day=1)
                    elif period == "quarterly":
                        due = current + timedelta(days=90)
                    else:
                        due = current.replace(year=current.year + 1)
                    
                    schedule.append({
                        "equipment": eq["type"],
                        "location": eq["location"],
                        "task": task["task"],
                        "due": due.strftime("%Y-%m-%d"),
                        "criticality": task["criticality"]
                    })
        
        return sorted(schedule, key=lambda x: x["due"])
    
    # ==================== ENERGY OPTIMIZATION ====================
    
    def optimize_energy(self, load_profile):
        """Calculate energy optimization opportunities"""
        peak = max(load_profile)
        avg = sum(load_profile) / len(load_profile)
        
        # Peak shaving potential
        if peak > avg * 1.5:
            battery = (peak - avg) * 2
            peak_shaving = True
        else:
            battery = 0
            peak_shaving = False
        
        # Savings calculation
        peak_hours = 4
        shed = peak * 0.2
        daily_savings = shed * peak_hours * self.energy_tariffs["peak"]["rate"]
        
        return {
            "peak_load": round(peak, 1),
            "avg_load": round(avg, 1),
            "peak_shaving": peak_shaving,
            "battery_kwh": round(battery, 1),
            "daily_savings": round(daily_savings, 2),
            "annual_savings": round(daily_savings * 365, 2),
            "recommendations": [
                "Install smart lighting controls",
                "Use VFDs for motors",
                "Schedule heavy loads during off-peak"
            ]
        }
    
    # ==================== QR CODE / ASSET TAGGING ====================
    
    def generate_asset_tag(self, asset_type, location):
        """Generate asset tag data"""
        asset_id = hashlib.md5(f"{asset_type}{location}{random.random()}".encode()).hexdigest()[:8]
        return {
            "asset_id": f"ELEC-{asset_id}",
            "type": asset_type,
            "location": location,
            "install_date": datetime.now().strftime("%Y-%m-%d"),
            "qr_data": f"https://maintenance.electrical.com/asset/{asset_id}"
        }

# ==================== STREAMLIT UI ====================

st.set_page_config(page_title="SG Electrical Design Pro", layout="wide")
engine = SGProEngine()

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/electrical.png", width=50)
    st.title("SG Electrical Pro")
    st.markdown("---")
    
    st.subheader("Project Info")
    project = st.text_input("Project Name", "My Building", key="project_name")
    location = st.text_input("Location", "Singapore", key="project_location")
    
    st.markdown("---")
    st.subheader("User Role")
    role = st.selectbox("Select Role", ["Installer", "Engineer", "Facility Manager"], key="user_role")
    
    st.markdown("---")
    st.info("Compliant with SS 638, SS 531, SS 555")

# Main tabs
tabs = st.tabs([
    "🏢 Room Design",
    "🔌 Cable & Tray",
    "🔄 Generator",
    "⚡ Lightning",
    "⛓️ Earthing",
    "📊 MSB Design",
    "🛠️ Maintenance",
    "📈 Analytics"
])

# ==================== TAB 1: ROOM DESIGN ====================
with tabs[0]:
    st.header("Complete Room Electrical Design")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Room Parameters")
        
        room_type = st.selectbox("Room Type", list(engine.lighting_standards.keys()), key="room_type_tab1")
        
        col_dim1, col_dim2, col_dim3 = st.columns(3)
        with col_dim1:
            length = st.number_input("Length (m)", 1.0, 50.0, 10.0, key="room_length")
        with col_dim2:
            width = st.number_input("Width (m)", 1.0, 50.0, 8.0, key="room_width")
        with col_dim3:
            height = st.number_input("Height (m)", 2.0, 20.0, 3.0, key="room_height")
        
        ac_status = st.radio("AC Status", ["Air Conditioned", "Non-AC"], key="ac_status")
        
        include_lighting = st.checkbox("Include Lighting", True, key="inc_lighting")
        include_sockets = st.checkbox("Include Sockets", True, key="inc_sockets")
        include_fans = st.checkbox("Include Fans", True, key="inc_fans")
        
        if st.button("Calculate Room Design", type="primary", key="calc_room"):
            with col2:
                st.subheader("Design Results")
                
                # Lighting
                if include_lighting:
                    st.write("### 💡 Lighting")
                    lighting = engine.calculate_lighting(room_type, length, width, height)
                    if lighting:
                        col_l1, col_l2, col_l3 = st.columns(3)
                        col_l1.metric("Fittings", lighting['num_fittings'])
                        col_l2.metric("Load", f"{lighting['total_watts']}W")
                        col_l3.metric("Lux", f"{lighting['lux_achieved']:.0f}")
                        
                        st.write(f"**Type:** {lighting['fitting_type']}")
                        st.write(f"**Layout:** {lighting['fittings_length']} × {lighting['fittings_width']}")
                        st.write(f"**Color:** {lighting['color_temp']}")
                
                # Sockets
                if include_sockets:
                    st.write("### 🔌 Sockets")
                    sockets = engine.calculate_sockets(room_type, length, width)
                    if sockets:
                        col_s1, col_s2, col_s3 = st.columns(3)
                        col_s1.metric("Sockets", sockets['num_sockets'])
                        col_s2.metric("Circuits", sockets['num_circuits'])
                        col_s3.metric("Load", f"{sockets['total_load_watts']/1000:.1f}kW")
                        
                        st.write(f"**Type:** {sockets['socket_type']}")
                        st.write(f"**Current/Phase:** {sockets['current_per_phase']}A")
                
                # Fans
                if include_fans:
                    st.write("### 🌀 Fans")
                    fans = engine.calculate_fans(room_type, length, width, height, "Air Conditioned" in ac_status)
                    if fans and fans['recommendations']:
                        st.metric("Required Airflow", f"{fans['required_cfm']:.0f} CFM")
                        for fan in fans['recommendations']:
                            st.write(f"**{fan['type']}:** {fan['quantity']} units, {fan['power']}W")
                
                # Isolators
                st.write("### 🔒 Isolators")
                equipment = []
                if include_lighting:
                    equipment.append("lighting")
                if include_sockets:
                    equipment.append("sockets")
                
                isolators = engine.get_isolators(room_type, equipment)
                for iso in isolators[:3]:  # Show first 3
                    st.write(f"**{iso['equipment']}:** {iso['type']}")

# ==================== TAB 2: CABLE & TRAY ====================
with tabs[1]:
    st.header("Cable & Tray Sizing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Voltage Drop Calculator")
        
        cable_size = st.selectbox("Cable Size (mm²)", list(engine.cable_impedance.keys()), key="vd_cable_size")
        current = st.number_input("Load Current (A)", 1.0, 1000.0, 100.0, key="vd_current")
        distance = st.number_input("Cable Length (m)", 1.0, 500.0, 50.0, key="vd_distance")
        pf = st.slider("Power Factor", 0.7, 1.0, 0.85, key="vd_pf")
        
        if st.button("Calculate Voltage Drop", key="calc_vd"):
            vd, vd_pct = engine.calculate_voltage_drop(cable_size, current, distance, pf)
            
            with col2:
                st.subheader("Results")
                if vd is not None:
                    st.metric("Voltage Drop", f"{vd}V")
                    st.metric("Percentage", f"{vd_pct}%")
                    
                    if vd_pct <= 4:
                        st.success("✅ Within acceptable limit (4%)")
                    else:
                        st.error("❌ Exceeds 4% limit - use larger cable")
    
    st.divider()
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("Cable Tray Sizing")
        
        num_cables = st.number_input("Number of Cable Types", 1, 5, 2, key="tray_num_cables")
        cables = []
        
        for i in range(num_cables):
            col_c, col_q = st.columns(2)
            with col_c:
                size = st.selectbox(f"Cable {i+1} Size", list(engine.cable_diameters.keys()), key=f"tray_cable_{i}")
            with col_q:
                qty = st.number_input(f"Qty {i+1}", 1, 100, 3, key=f"tray_qty_{i}")
            
            for _ in range(qty):
                cables.append(size)
        
        tray_depth = st.selectbox("Tray Depth (mm)", [50, 75, 100, 150], key="tray_depth")
        tray_type = st.selectbox("Tray Type", ["perforated", "ladder", "solid"], key="tray_type")
        spare = st.slider("Spare Capacity %", 0, 50, 25, key="tray_spare") / 100
        
        if st.button("Size Tray", key="calc_tray"):
            result = engine.calculate_tray(cables, tray_depth, tray_type, spare)
            
            with col4:
                st.subheader("Tray Results")
                st.metric("Total Cable Area", f"{result['total_area']} mm²")
                st.metric("Required Width", f"{result['required_width']} mm")
                st.metric("Selected Tray", f"{result['selected_width']} mm")
                st.metric("Fill Percentage", f"{result['actual_fill']}%")
                
                if result['actual_fill'] <= result['fill_factor']:
                    st.success("✅ Tray size OK")
                else:
                    st.error("❌ Tray overfilled - increase size")

# ==================== TAB 3: GENERATOR ====================
with tabs[2]:
    st.header("Generator Sizing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Essential Loads")
        
        num_lifts = st.number_input("Number of Lifts", 0, 10, 2, key="gen_num_lifts")
        essential = []
        starting = []
        
        for i in range(num_lifts):
            lift_kw = st.number_input(f"Lift {i+1} (kW)", 0.0, 100.0, 10.0, key=f"gen_lift_{i}")
            running = lift_kw / 0.85  # Approx kVA
            essential.append(running)
            starting.append(running * 2.5)  # Starting multiplier
        
        num_ess = st.number_input("Other Essential Loads", 0, 10, 2, key="gen_num_ess")
        for i in range(num_ess):
            load = st.number_input(f"Essential Load {i+1} (kVA)", 0.0, 100.0, 5.0, key=f"gen_ess_{i}")
            essential.append(load)
    
    with col2:
        st.subheader("Fire Loads")
        
        has_pump = st.checkbox("Include Fire Pump", True, key="gen_has_pump")
        fire = []
        fire_start = []
        
        if has_pump:
            pump_kw = st.number_input("Fire Pump (kW)", 0.0, 200.0, 30.0, key="gen_pump_kw")
            pump_type = st.selectbox("Starting Type", ["Direct Online", "Star-Delta", "Soft Starter"], key="gen_pump_type")
            
            running = pump_kw / 0.85
            multiplier = {"Direct Online": 6.0, "Star-Delta": 3.5, "Soft Starter": 2.5}[pump_type]
            
            fire.append(running)
            fire_start.append(running * multiplier)
        
        num_fans = st.number_input("Pressurization Fans", 0, 10, 2, key="gen_num_fans")
        for i in range(num_fans):
            fan_kw = st.number_input(f"Fan {i+1} (kW)", 0.0, 50.0, 5.5, key=f"gen_fan_{i}")
            running = fan_kw / 0.85
            fire.append(running)
            fire_start.append(running * 3.0)  # Fan starting
    
    if st.button("Size Generator", key="calc_gen"):
        all_start = starting + fire_start
        largest = max(all_start) if all_start else 0
        
        gen = engine.calculate_generator(essential, fire, largest)
        
        st.success(f"### Recommended Generator: {gen['recommended_kva']} kVA")
        
        col_g1, col_g2, col_g3 = st.columns(3)
        col_g1.metric("Running Load", f"{gen['running_kva']} kVA")
        col_g2.metric("Starting Load", f"{gen['starting_kva']} kVA")
        col_g3.metric("Required", f"{gen['required_kva']} kVA")

# ==================== TAB 4: LIGHTNING ====================
with tabs[3]:
    st.header("Lightning Protection")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Building Parameters")
        
        b_length = st.number_input("Length (m)", 1.0, 200.0, 50.0, key="lp_length")
        b_width = st.number_input("Width (m)", 1.0, 200.0, 30.0, key="lp_width")
        b_height = st.number_input("Height (m)", 1.0, 100.0, 15.0, key="lp_height")
        b_roof = st.selectbox("Roof Type", ["Flat", "Pitched"], key="lp_roof")
        b_level = st.selectbox("Protection Level", ["Level I", "Level II", "Level III", "Level IV"], index=2, key="lp_level")
        
        if st.button("Calculate Lightning Protection", key="calc_lp"):
            lp = engine.calculate_lightning(b_length, b_width, b_height, b_level, b_roof)
            
            with col2:
                st.subheader("Results")
                
                col_l1, col_l2, col_l3 = st.columns(3)
                col_l1.metric("Air Terminals", lp['num_terminals'])
                col_l2.metric("Down Conductors", lp['num_down_conductors'])
                col_l3.metric("Test Joints", lp['num_test_joints'])
                
                st.write(f"**Building Area:** {lp['area']:.0f} m²")
                st.write(f"**Terminal Spacing:** {lp['terminal_spacing']} m")
                st.write(f"**Protection Angle:** {lp['protection_params']['protection_angle']}°")
                st.write(f"**Mesh Size:** {lp['protection_params']['mesh_size']} m")

# ==================== TAB 5: EARTHING ====================
with tabs[4]:
    st.header("Earthing System")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Earth Pit Calculation")
        
        b_area = st.number_input("Building Area (m²)", 1.0, 10000.0, 1500.0, key="earth_area")
        has_fuel = st.checkbox("Has Fuel Tank", True, key="earth_fuel")
        soil = st.selectbox("Soil Condition", ["Normal", "Poor"], key="earth_soil")
        level = st.selectbox("Protection Level", ["Level I", "Level II", "Level III", "Level IV"], index=2, key="earth_level")
        
        if st.button("Calculate Earth Pits", key="calc_earth"):
            pits = engine.calculate_earth_pits(b_area, has_fuel, soil, level)
            
            with col2:
                st.subheader("Results")
                
                col_p1, col_p2, col_p3 = st.columns(3)
                col_p1.metric("Generator", f"{pits['generator']} pits")
                col_p2.metric("Fuel Tank", f"{pits['fuel_tank']} pits")
                col_p3.metric("Lightning", f"{pits['lightning']} pits")
                
                st.success(f"### Total Required: {pits['total']} earth pits")
                
                st.info("**Specifications:**")
                st.write("- Depth: 3m minimum")
                st.write("- Electrode: 20mm φ copper-clad")
                st.write("- Resistance: <1Ω combined")

# ==================== TAB 6: MSB DESIGN ====================
with tabs[5]:
    st.header("Main Switchboard Design")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Incomer Sizing")
        
        total_load = st.number_input("Total Load (kW)", 1.0, 2000.0, 400.0, key="msb_load")
        pf = st.slider("Power Factor", 0.7, 1.0, 0.85, key="msb_pf")
        voltage = 400
        
        ib = (total_load * 1000) / (math.sqrt(3) * voltage * pf)
        
        at, af = engine.get_at_af(ib)
        breaker_type = "ACB" if af >= 800 else "MCCB" if af > 63 else "MCB"
        
        st.metric("Design Current (Ib)", f"{ib:.1f} A")
        st.success(f"**Incomer:** {at}AT / {af}AF {breaker_type}")
        
        # Cable selection
        cable_len = st.number_input("Cable Length (m)", 1.0, 200.0, 50.0, key="msb_cable_len")
        max_vd = st.slider("Max V.D. %", 1.0, 8.0, 4.0, key="msb_max_vd")
        
        cable = engine.select_cable(ib, cable_len, pf, max_vd)
        
        if "error" in cable:
            st.error(cable["error"])
        else:
            st.write(f"**Cable:** {cable['size']} mm² (Iz={cable['iz']}A)")
            st.write(f"**V.D.:** {cable['vd']}V ({cable['vd_percent']}%)")
            if "warning" in cable:
                st.warning(cable["warning"])
    
    with col2:
        st.subheader("Physical Layout")
        
        num_feeder = st.number_input("No. of Feeders", 1, 20, 5, key="msb_feeders")
        width = (800 if breaker_type == "ACB" else 600) + num_feeder * 400
        width = width * 1.2  # 20% spare
        
        st.metric("Estimated Width", f"{width:.0f} mm")
        
        st.write("**Clearance Requirements:**")
        clearances = pd.DataFrame({
            "Position": ["Front", "Rear", "Sides", "Top"],
            "Min (mm)": [1500, 800, 800, 500]
        })
        st.table(clearances)

# ==================== TAB 7: MAINTENANCE ====================
with tabs[6]:
    st.header("Maintenance Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Predictive Maintenance")
        
        equip = st.selectbox("Equipment", list(engine.equipment_lifetime.keys()), key="maint_equip")
        hours = st.slider("Operating Hours", 0, 50000, 10000, key="maint_hours")
        last = st.date_input("Last Service", datetime.now() - timedelta(days=180), key="maint_last")
        
        if st.button("Check Status", key="check_maint"):
            pred = engine.predict_maintenance(equip, hours, datetime.combine(last, datetime.min.time()))
            
            with col2:
                st.subheader("Equipment Health")
                
                status_color = {"Good": "🟢", "Warning": "🟡", "Critical": "🔴"}
                st.metric("Status", f"{status_color.get(pred['status'], '⚪')} {pred['status']}")
                st.write(f"**Next:** {pred['next_maintenance']}")
                
                st.write("**Recommendations:**")
                for rec in pred['recommendations']:
                    st.write(f"- {rec}")
                
                if pred['status'] == "Critical":
                    st.error("⚠️ Immediate action required!")
    
    st.divider()
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("Maintenance Schedule")
        
        equipment_list = [
            {"type": "Generator", "location": "Gen Room"},
            {"type": "UPS Battery", "location": "Elec Room"},
            {"type": "MCB/MCCB", "location": "MSB"}
        ]
        
        schedule = engine.generate_schedule(equipment_list, datetime.now().strftime("%Y-%m-%d"))
        
        # Show next 5 tasks
        for task in schedule[:5]:
            st.write(f"**{task['due']}:** {task['task']}")
            st.write(f"_{task['equipment']} - {task['criticality']}_")
            st.divider()
    
    with col4:
        st.subheader("Asset Tags")
        
        asset_types = ["Generator", "MSB", "Lighting Panel", "Fire Pump"]
        for asset in asset_types:
            tag = engine.generate_asset_tag(asset, "Site")
            st.write(f"**{asset}:** {tag['asset_id']}")
            st.code(tag['qr_data'], language=None)

# ==================== TAB 8: ANALYTICS ====================
with tabs[7]:
    st.header("Energy Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Load Profile")
        
        # Generate sample data
        hours = list(range(24))
        load = [100 + 50 * math.sin(i/4) + random.uniform(-10, 10) for i in hours]
        
        fig = px.line(x=hours, y=load, 
                     title="Daily Load Profile",
                     labels={'x': 'Hour', 'y': 'Load (kW)'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Optimization")
        
        opt = engine.optimize_energy(load)
        
        col_o1, col_o2 = st.columns(2)
        col_o1.metric("Peak Load", f"{opt['peak_load']} kW")
        col_o2.metric("Avg Load", f"{opt['avg_load']} kW")
        
        st.metric("Annual Savings Potential", f"${opt['annual_savings']:,.0f}")
        
        if opt['peak_shaving']:
            st.info(f"💡 Consider {opt['battery_kwh']} kWh battery for peak shaving")
        
        st.write("**Recommendations:**")
        for rec in opt['recommendations']:
            st.write(f"- {rec}")
    
    st.divider()
    
    st.subheader("Cost Analysis")
    
    # Tariff table
    tariff_df = pd.DataFrame([
        {"Period": k.replace('_', ' ').title(), 
         "Time": v["time"], 
         "Rate ($/kWh)": v["rate"]}
        for k, v in engine.energy_tariffs.items()
    ])
    st.table(tariff_df)

# Footer
st.markdown("---")
st.caption("© SG Electrical Design Pro | Compliant with Singapore Standards SS 638, SS 531, SS 555 | Version 3.0")
