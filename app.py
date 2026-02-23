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
            },
            "Market": {
                "recommended_lux": 300,
                "led_watt_per_m2": 10,
                "fitting_type": "LED Highbay / Vapor-tight",
                "lumens_per_fitting": 10000,
                "watt_per_fitting": 100,
                "mounting_height": "4-6m",
                "color_temp": "4000K",
                "cri_requirement": ">80",
                "ip_rating": "IP65"
            },
            "Exhibition Hall": {
                "recommended_lux": 300,
                "led_watt_per_m2": 12,
                "fitting_type": "LED Highbay / Track Light",
                "lumens_per_fitting": 15000,
                "watt_per_fitting": 150,
                "mounting_height": "6-12m",
                "color_temp": "4000K",
                "cri_requirement": ">90"
            },
            "Sports Hall": {
                "recommended_lux": 500,
                "led_watt_per_m2": 15,
                "fitting_type": "LED Sports Light",
                "lumens_per_fitting": 25000,
                "watt_per_fitting": 250,
                "mounting_height": "8-15m",
                "color_temp": "5000K",
                "cri_requirement": ">80"
            },
            "Factory / Industrial": {
                "recommended_lux": 300,
                "led_watt_per_m2": 10,
                "fitting_type": "LED Industrial Highbay",
                "lumens_per_fitting": 20000,
                "watt_per_fitting": 200,
                "mounting_height": "6-12m",
                "color_temp": "5000K",
                "cri_requirement": ">70",
                "ip_rating": "IP65"
            },
            "Airport / Terminal": {
                "recommended_lux": 300,
                "led_watt_per_m2": 12,
                "fitting_type": "LED Linear / Highbay",
                "lumens_per_fitting": 15000,
                "watt_per_fitting": 150,
                "mounting_height": "8-15m",
                "color_temp": "4000K",
                "cri_requirement": ">80"
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
            },
            "Market": {
                "density": "1 socket per stall (minimum 2)",
                "spacing": "At each stall location",
                "type": "13A BS 1363, IP66 weatherproof",
                "circuit_rating": "20A radial per stall",
                "max_sockets_per_circuit": 2,
                "special_requirements": ["Weatherproof covers", "Individual RCBO", "High temperature rating"]
            },
            "Exhibition Hall": {
                "density": "1 socket per 20m²",
                "spacing": "Floor boxes every 5m grid",
                "type": "16A / 32A commando sockets",
                "circuit_rating": "Individual circuits",
                "max_sockets_per_circuit": 4,
                "special_requirements": ["Floor boxes", "Trunking systems", "3-phase supplies"]
            },
            "Factory / Industrial": {
                "density": "As per machinery layout",
                "spacing": "Along columns every 5-10m",
                "type": "16A / 32A / 63A industrial sockets",
                "circuit_rating": "Individual circuits",
                "max_sockets_per_circuit": 2,
                "special_requirements": ["3-phase supplies", "High current capacity", "Armoured cables"]
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
            },
            "Industrial Machine": {
                "required": True,
                "type": "Local isolator with lockable handle",
                "location": "At machine, visible",
                "purpose": "Lockout/tagout for maintenance"
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
                "suitable_for": ["Hawker Centre", "Market", "Warehouse", "Factory", "Exhibition Hall", "Sports Hall", "Airport"],
                "blade_diameter": ["8ft (2.4m)", "10ft (3.0m)", "12ft (3.7m)", "16ft (4.9m)", "20ft (6.1m)", "24ft (7.3m)"],
                "coverage_area_m2": {
                    "8ft": 150,
                    "10ft": 250,
                    "12ft": 350,
                    "16ft": 600,
                    "20ft": 900,
                    "24ft": 1200
                },
                "airflow_cfm": {
                    "8ft": 30000,
                    "10ft": 45000,
                    "12ft": 60000,
                    "16ft": 90000,
                    "20ft": 120000,
                    "24ft": 150000
                },
                "power_watts": {
                    "8ft": 300,
                    "10ft": 500,
                    "12ft": 800,
                    "16ft": 1200,
                    "20ft": 1500,
                    "24ft": 2000
                },
                "mounting_height": "Minimum 4m, ideal 6-15m",
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
            "Industrial Pedestal Fan": {
                "suitable_for": ["Factory", "Warehouse", "Loading Bay"],
                "blade_diameter": ["24\" (600mm)", "30\" (750mm)", "36\" (900mm)"],
                "coverage_area_m2": {
                    "24\"": 50,
                    "30\"": 80,
                    "36\"": 120
                },
                "airflow_cfm": {
                    "24\"": 12000,
                    "30\"": 18000,
                    "36\"": 25000
                },
                "power_watts": {
                    "24\"": 400,
                    "30\"": 600,
                    "36\"": 800
                },
                "mounting_height": "Floor standing",
                "noise_level": "High",
                "speed_control": "3-speed switch"
            },
            "Exhaust Fan (Wall/Ceiling)": {
                "suitable_for": ["Toilet", "Kitchen", "Store Room", "Plant Room"],
                "blade_diameter": ["6\" (150mm)", "8\" (200mm)", "10\" (250mm)", "12\" (300mm)", "16\" (400mm)", "20\" (500mm)"],
                "airflow_cfm": {
                    "6\"": 150,
                    "8\"": 300,
                    "10\"": 500,
                    "12\"": 800,
                    "16\"": 1500,
                    "20\"": 2500
                },
                "power_watts": {
                    "6\"": 20,
                    "8\"": 35,
                    "10\"": 50,
                    "12\"": 80,
                    "16\"": 150,
                    "20\"": 250
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
            "Market": {"ac_ach": 0, "non_ac_ach": 12, "notes": "High ceiling, mechanical extraction"},
            "Exhibition Hall": {"ac_ach": 6, "non_ac_ach": 10, "notes": "Variable occupancy"},
            "Sports Hall": {"ac_ach": 8, "non_ac_ach": 12, "notes": "High activity level"},
            "Factory": {"ac_ach": 4, "non_ac_ach": 8, "notes": "Heat removal from machinery"},
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
        
        # ==================== EV CHARGER CONFIGURATION ====================
        self.ev_charger_config = {
            "percentage_requirement": 15,  # 15% of total lots
            "power_per_charger_kw": 7.0,   # 7kW per charger (typical for AC charging)
            "charger_types": {
                "AC Level 2": {"power": 7, "voltage": 230, "phases": 1, "current": 32},
                "AC Fast": {"power": 22, "voltage": 400, "phases": 3, "current": 32},
                "DC Fast": {"power": 50, "voltage": 400, "phases": 3, "current": 80}
            },
            "diversity_factor": 0.6,  # Not all chargers will be used simultaneously
            "efficiency": 0.95,  # Charger efficiency
            "power_factor": 0.98  # Typical for modern EV chargers
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
            "Lightning Arrester": 10,  # years
            "EV Charger": 10,  # years
            "EV Charger Cable": 5,  # years
            "Industrial Machine": 15,  # years
            "HVLS Fan": 15  # years
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
                {"task": "Emergency lighting test", "duration_min": 20, "criticality": "High"},
                {"task": "EV charger visual inspection", "duration_min": 30, "criticality": "Medium"},
                {"task": "HVLS fan check", "duration_min": 30, "criticality": "Medium"}
            ],
            "monthly": [
                {"task": "Earth resistance measurement", "duration_min": 60, "criticality": "High"},
                {"task": "Circuit breaker exercise", "duration_min": 45, "criticality": "Medium"},
                {"task": "Thermal imaging scan", "duration_min": 90, "criticality": "High"},
                {"task": "EV charger functional test", "duration_min": 60, "criticality": "Medium"}
            ],
            "quarterly": [
                {"task": "Insulation resistance test", "duration_min": 180, "criticality": "High"},
                {"task": "Protection relay calibration", "duration_min": 240, "criticality": "High"},
                {"task": "Battery load test", "duration_min": 60, "criticality": "High"}
            ],
            "annually": [
                {"task": "Full load generator test", "duration_min": 240, "criticality": "High"},
                {"task": "Oil and filter change", "duration_min": 120, "criticality": "High"},
                {"task": "Professional inspection", "duration_min": 480, "criticality": "High"},
                {"task": "EV charger calibration check", "duration_min": 120, "criticality": "Medium"},
                {"task": "HVLS fan bearing check", "duration_min": 120, "criticality": "Medium"}
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
    
    def calculate_ev_chargers(self, total_carpark_lots, charger_type="AC Level 2"):
        """
        Calculate EV charger requirements based on 15% of total carpark lots
        Each charger: 7kW as per requirement
        """
        # Calculate number of chargers (15% of total lots, rounded up)
        num_chargers = math.ceil(total_carpark_lots * self.ev_charger_config["percentage_requirement"] / 100)
        
        # Get charger specifications
        charger_spec = self.ev_charger_config["charger_types"].get(charger_type, 
                                                                   self.ev_charger_config["charger_types"]["AC Level 2"])
        
        # Calculate total load
        total_load_kw = num_chargers * self.ev_charger_config["power_per_charger_kw"]
        
        # Apply diversity factor (not all chargers will be in use simultaneously)
        diversified_load_kw = total_load_kw * self.ev_charger_config["diversity_factor"]
        
        # Calculate current requirements
        if charger_spec["phases"] == 3:
            current_per_charger = (charger_spec["power"] * 1000) / (math.sqrt(3) * charger_spec["voltage"] * self.ev_charger_config["power_factor"])
        else:
            current_per_charger = (charger_spec["power"] * 1000) / (charger_spec["voltage"] * self.ev_charger_config["power_factor"])
        
        total_current = current_per_charger * num_chargers * self.ev_charger_config["diversity_factor"]
        
        # Calculate number of circuits (assuming 8 chargers per 3-phase circuit max)
        chargers_per_circuit = 8
        num_circuits = math.ceil(num_chargers / chargers_per_circuit)
        
        return {
            "total_carpark_lots": total_carpark_lots,
            "percentage_required": self.ev_charger_config["percentage_requirement"],
            "num_chargers": num_chargers,
            "charger_type": charger_type,
            "power_per_charger_kw": self.ev_charger_config["power_per_charger_kw"],
            "total_load_kw": round(total_load_kw, 1),
            "diversified_load_kw": round(diversified_load_kw, 1),
            "total_current_a": round(total_current, 1),
            "num_circuits": num_circuits,
            "chargers_per_circuit": chargers_per_circuit,
            "diversity_factor": self.ev_charger_config["diversity_factor"],
            "power_factor": self.ev_charger_config["power_factor"],
            "efficiency": self.ev_charger_config["efficiency"],
            "annual_energy_kwh": round(total_load_kw * 8 * 365 * self.ev_charger_config["diversity_factor"], 0),  # Assuming 8 hours usage per day
            "recommendations": [
                f"Install {num_circuits} dedicated circuits for EV chargers",
                "Use Type B RCD for DC leakage protection",
                "Consider smart charging for load management",
                "Install energy metering for billing if required"
            ]
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
            "Hawker Centre": ["Stall (Hawker Centre)"],
            "Market": ["Stall (Hawker Centre)"],
            "Factory / Industrial": ["Industrial Machine"],
            "Warehouse / Store": ["Industrial Machine"]
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
        """Calculate fan requirements for large spaces"""
        area = length * width
        volume = area * height
        
        # Get ventilation requirements
        vent = self.ventilation_requirements.get(room_type, 
              self.ventilation_requirements.get("Office", {"ac_ach": 6, "non_ac_ach": 8, "notes": ""}))
        
        ach = vent["ac_ach"] if is_aircond else vent["non_ac_ach"]
        required_cfm = volume * ach * 0.588
        
        recommendations = []
        
        # For very large spaces (>=1000m²), recommend multiple HVLS fans or combination
        if area >= 1000:
            hvls = self.fan_database["High Volume Low Speed (HVLS)"]
            
            # Try largest HVLS fans first
            for size in ["24ft", "20ft", "16ft", "12ft"]:
                if size in hvls["coverage_area_m2"]:
                    coverage = hvls["coverage_area_m2"][size]
                    num_fans = math.ceil(area / coverage)
                    
                    # For very large areas, don't exceed practical number of fans
                    if num_fans <= 12:  # Reasonable max
                        recommendations.append({
                            "type": f"HVLS Fan ({size})",
                            "size": size,
                            "quantity": num_fans,
                            "power": num_fans * hvls["power_watts"][size],
                            "airflow": num_fans * hvls["airflow_cfm"][size],
                            "mounting": hvls["mounting_height"],
                            "coverage_per_fan": coverage
                        })
                        break
            
            # If still need more airflow, add industrial pedestal fans
            if recommendations and recommendations[0]["airflow"] < required_cfm:
                remaining_cfm = required_cfm - recommendations[0]["airflow"]
                industrial = self.fan_database["Industrial Pedestal Fan"]
                num_industrial = math.ceil(remaining_cfm / 25000)  # Using largest industrial fan
                recommendations.append({
                    "type": "Industrial Pedestal Fan",
                    "quantity": num_industrial,
                    "power": num_industrial * 800,
                    "airflow": num_industrial * 25000,
                    "purpose": "Supplemental air movement"
                })
        
        # HVLS for large spaces (150-1000m²)
        elif height >= 4 and area >= 150:
            hvls = self.fan_database["High Volume Low Speed (HVLS)"]
            for size in ["20ft", "16ft", "12ft", "10ft", "8ft"]:
                if size in hvls["coverage_area_m2"] and hvls["coverage_area_m2"][size] >= area * 0.8:
                    num_fans = math.ceil(area / hvls["coverage_area_m2"][size])
                    recommendations.append({
                        "type": f"HVLS Fan ({size})",
                        "size": size,
                        "quantity": num_fans,
                        "power": num_fans * hvls["power_watts"][size],
                        "airflow": num_fans * hvls["airflow_cfm"][size],
                        "mounting": hvls["mounting_height"]
                    })
                    break
        
        # Ceiling fans for medium spaces
        elif height <= 4 and area <= 500:
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
        
        # Wall mounted fans for workshops, kitchens
        if "Kitchen" in room_type or "Workshop" in room_type or "Factory" in room_type:
            wall = self.fan_database["Wall Mounted Fan (Oscillating)"]
            num = math.ceil(area / 100) 
