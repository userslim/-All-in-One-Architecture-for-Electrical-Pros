import streamlit as st
import math
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import hashlib
import random

class SGProEngine:
    def __init__(self):
        # [Previous initialization code remains the same...]
        self.standard_frames = [63, 100, 125, 160, 250, 400, 630, 800, 1000, 1250, 1600, 2000, 2500, 3200, 4000]
        self.standard_trips = [6, 10, 16, 20, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 320, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3200, 4000]
        
        # Cable Iz (Current Capacity) for Cu/XLPE/SWA/PVC - Table 4E4A (SS 638)
        self.cable_db = {
            1.5: 25, 2.5: 33, 4: 43, 6: 56, 10: 77, 16: 102, 25: 135, 35: 166, 
            50: 201, 70: 255, 95: 309, 120: 358, 150: 410, 185: 469, 240: 551, 300: 627,
            400: 750, 500: 860, 630: 980
        }
        
        # Cable diameter database
        self.cable_diameters = {
            1.5: 12, 2.5: 13, 4: 14, 6: 15, 10: 17, 16: 19, 25: 22, 35: 24,
            50: 27, 70: 30, 95: 33, 120: 36, 150: 39, 185: 42, 240: 46, 300: 50,
            400: 55, 500: 60, 630: 65
        }
        
        # Cable resistance and reactance
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
        
        # Lighting design database
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
            "Laboratory": {
                "recommended_lux": 750,
                "led_watt_per_m2": 18,
                "fitting_type": "LED Cleanroom / Sealed",
                "lumens_per_fitting": 5000,
                "watt_per_fitting": 50,
                "mounting_height": "3m",
                "color_temp": "5000K",
                "cri_requirement": ">90"
            },
            "Gym / Fitness": {
                "recommended_lux": 300,
                "led_watt_per_m2": 10,
                "fitting_type": "LED Highbay / Batten",
                "lumens_per_fitting": 8000,
                "watt_per_fitting": 80,
                "mounting_height": "4-6m",
                "color_temp": "5000K",
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
            "Plant Room / Technical": {
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
                "fitting_type": "LED Highbay / Batten",
                "lumens_per_fitting": 8000,
                "watt_per_fitting": 80,
                "mounting_height": "4-6m",
                "color_temp": "4000K",
                "cri_requirement": ">80"
            }
        }
        
        # Socket outlet requirements
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
            "Warehouse": {
                "density": "1 socket per 50m²",
                "spacing": "Along columns and walls",
                "type": "13A BS 1363, 1-gang heavy duty",
                "circuit_rating": "20A radial",
                "max_sockets_per_circuit": 4,
                "special_requirements": ["Impact resistant", "High level sockets for MHE charging"]
            },
            "Classroom": {
                "density": "2 double sockets per wall",
                "spacing": "Front and back of room",
                "type": "13A BS 1363, 2-gang",
                "circuit_rating": "20A ring circuit",
                "max_sockets_per_circuit": 8,
                "special_requirements": ["Teacher's desk sockets", "AV equipment points"]
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
                "special_requirements": ["Weatherproof covers", "Individual RCBO"]
            }
        }
        
        # Isolator requirements
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
            "Air Conditioner (Cassette)": {
                "required": True,
                "type": "45A Isolator with switch",
                "location": "Near controller, accessible",
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
            "Switchboard": {
                "required": True,
                "type": "Main breaker",
                "location": "At switchboard",
                "purpose": "Main isolation"
            },
            "Fan (Ceiling)": {
                "required": False,
                "type": "Regulator/switch only",
                "location": "Wall mounted",
                "purpose": "Speed control"
            },
            "Fan (Industrial)": {
                "required": True,
                "type": "32A Isolator with switch",
                "location": "Near fan, accessible",
                "purpose": "Maintenance isolation"
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
            "Solar Inverter": {
                "required": True,
                "type": "AC Isolator + DC Isolator",
                "location": "Near inverter",
                "purpose": "Complete isolation for maintenance"
            },
            "Battery Storage": {
                "required": True,
                "type": "DC Isolator + AC Isolator",
                "location": "At battery enclosure",
                "purpose": "Emergency disconnect"
            }
        }
        
        # Fan database
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
            "Pedestal Fan": {
                "suitable_for": ["Temporary areas", "Store", "Event"],
                "blade_diameter": ["16\" (400mm)", "18\" (450mm)", "20\" (500mm)"],
                "coverage_area_m2": 20,
                "airflow_cfm": 3000,
                "power_watts": 80,
                "mounting_height": "Floor standing",
                "noise_level": "Medium",
                "speed_control": "3-speed"
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
            },
            "Jet Fan (Car Park)": {
                "suitable_for": ["Car Park", "Tunnel"],
                "thrust_rating": ["25N", "35N", "45N"],
                "airflow_cfm": {
                    "25N": 8000,
                    "35N": 12000,
                    "45N": 16000
                },
                "power_watts": {
                    "25N": 550,
                    "35N": 750,
                    "45N": 1100
                },
                "mounting_height": "Below ceiling",
                "noise_level": "High",
                "speed_control": "VFD / Multi-speed",
                "purpose": "Smoke clearance and ventilation"
            }
        }
        
        # Ventilation requirements
        self.ventilation_requirements = {
            "Office": {"ac_ach": 6, "non_ac_ach": 8, "notes": "Fresh air requirement 10 L/s/person"},
            "Meeting Room": {"ac_ach": 8, "non_ac_ach": 12, "notes": "Higher occupancy, smoking room separate"},
            "Corridor": {"ac_ach": 2, "non_ac_ach": 4, "notes": "Natural ventilation if possible"},
            "Staircase": {"ac_ach": 2, "non_ac_ach": 4, "notes": "Pressurization for fire safety"},
            "Car Park": {"ac_ach": 0, "non_ac_ach": 6, "notes": "CO monitoring required, jet fans"},
            "Restaurant": {"ac_ach": 8, "non_ac_ach": 15, "notes": "Kitchen separate exhaust"},
            "Kitchen": {"ac_ach": 15, "non_ac_ach": 30, "notes": "Kitchen hood required"},
            "Toilet": {"ac_ach": 10, "non_ac_ach": 15, "notes": "Mechanical exhaust mandatory"},
            "Warehouse": {"ac_ach": 2, "non_ac_ach": 4, "notes": "Ventilation for heat removal"},
            "Hawker Centre": {"ac_ach": 0, "non_ac_ach": 12, "notes": "High ceiling, mechanical extraction"},
            "Market": {"ac_ach": 0, "non_ac_ach": 10, "notes": "Odour control, ventilation"},
            "Plant Room": {"ac_ach": 10, "non_ac_ach": 15, "notes": "Heat removal for equipment"},
            "Generator Room": {"ac_ach": 20, "non_ac_ach": 30, "notes": "Combustion air + cooling"},
            "Battery Room": {"ac_ach": 12, "non_ac_ach": 15, "notes": "Hydrogen gas extraction"},
            "Electrical Switchroom": {"ac_ach": 6, "non_ac_ach": 8, "notes": "Temperature control <35°C"},
            "EV Charging Station": {"ac_ach": 4, "non_ac_ach": 8, "notes": "Ventilation for battery cooling"},
            "Solar Inverter Room": {"ac_ach": 8, "non_ac_ach": 12, "notes": "Heat dissipation"}
        }
        
        # Motor starting multipliers
        self.motor_starting_multipliers = {
            "Lift (Variable Speed)": 2.5,
            "Lift (Star-Delta)": 3.0,
            "Fire Pump (Direct Online)": 6.0,
            "Fire Pump (Star-Delta)": 3.5,
            "Fire Pump (Soft Starter)": 2.5,
            "HVAC Chiller": 2.0,
            "Pressurization Fan": 3.0,
            "AHU Fan": 2.5,
            "Water Pump": 4.0,
            "Jet Fan": 3.0,
            "Exhaust Fan": 2.5
        }
        
        # Lightning protection standards
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
        
        # Cable tray fill factors
        self.tray_fill_factors = {
            "perforated": 0.4,
            "ladder": 0.4,
            "solid": 0.3,
            "wire_mesh": 0.35
        }
        
        # Standard tray sizes
        self.standard_tray_sizes = [50, 100, 150, 200, 300, 400, 450, 500, 600, 750, 900]
        
        # ==================== NEW AUTOMATION FEATURES ====================
        
        # BIM Integration Data Structure
        self.bim_data = {
            "project_info": {},
            "equipment_inventory": [],
            "cable_schedule": [],
            "panel_schedule": [],
            "lighting_controls": [],
            "maintenance_tasks": [],
            "test_records": [],
            "alerts": []
        }
        
        # IoT Sensor Configuration
        self.iot_sensor_types = {
            "temperature": {"unit": "°C", "min": 0, "max": 50, "alert_threshold": 40},
            "humidity": {"unit": "%", "min": 0, "max": 100, "alert_threshold": 85},
            "current": {"unit": "A", "min": 0, "max": 1000, "alert_threshold": 0.9},  # 90% of rating
            "voltage": {"unit": "V", "min": 0, "max": 500, "alert_threshold": 0.9},
            "power": {"unit": "kW", "min": 0, "max": 500, "alert_threshold": 0.9},
            "earth_resistance": {"unit": "Ω", "min": 0, "max": 10, "alert_threshold": 1},
            "insulation_resistance": {"unit": "MΩ", "min": 0, "max": 1000, "alert_threshold": 1},
            "lux_level": {"unit": "lx", "min": 0, "max": 1000, "alert_threshold": 0.7},  # 70% of design
            "airflow": {"unit": "CFM", "min": 0, "max": 50000, "alert_threshold": 0.8}
        }
        
        # Smart Building Integration
        self.bms_protocols = ["BACnet", "Modbus", "KNX", "LonWorks", "MQTT", "OPC UA"]
        
        # Energy Management Features
        self.energy_tariffs = {
            "peak": {"time": "9am-12pm, 6pm-8pm", "rate": 0.30},
            "off_peak": {"time": "10pm-7am", "rate": 0.15},
            "normal": {"time": "Others", "rate": 0.22}
        }
        
        # Predictive Maintenance Models
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
        
        # Digital Twin Parameters
        self.digital_twin_config = {
            "update_frequency": "Real-time",
            "data_retention_days": 365,
            "simulation_capabilities": ["Load flow", "Short circuit", "Voltage drop", "Energy optimization"],
            "ml_models": ["Load prediction", "Failure prediction", "Energy optimization"]
        }
        
        # Maintenance Templates
        self.maintenance_templates = {
            "daily": [
                {"task": "Generator visual check", "duration_min": 15, "criticality": "High"},
                {"task": "Battery charger status", "duration_min": 5, "criticality": "Medium"},
                {"task": "Fuel level check", "duration_min": 5, "criticality": "High"},
                {"task": "Alarm panel check", "duration_min": 10, "criticality": "High"},
                {"task": "Switchroom temperature", "duration_min": 5, "criticality": "Medium"}
            ],
            "weekly": [
                {"task": "Generator run test (30 mins)", "duration_min": 45, "criticality": "High"},
                {"task": "Battery voltage measurement", "duration_min": 15, "criticality": "Medium"},
                {"task": "Coolant level check", "duration_min": 10, "criticality": "Medium"},
                {"task": "Emergency lighting test", "duration_min": 20, "criticality": "High"},
                {"task": "Fire pump test run", "duration_min": 15, "criticality": "High"}
            ],
            "monthly": [
                {"task": "Earth resistance measurement", "duration_min": 60, "criticality": "High"},
                {"task": "Load bank test", "duration_min": 120, "criticality": "High"},
                {"task": "Circuit breaker exercise", "duration_min": 45, "criticality": "Medium"},
                {"task": "Thermal imaging scan", "duration_min": 90, "criticality": "High"},
                {"task": "UPS battery test", "duration_min": 30, "criticality": "High"}
            ],
            "quarterly": [
                {"task": "Insulation resistance test", "duration_min": 180, "criticality": "High"},
                {"task": "Protection relay calibration", "duration_min": 240, "criticality": "High"},
                {"task": "Battery load test", "duration_min": 60, "criticality": "High"},
                {"task": "Fuel system check", "duration_min": 45, "criticality": "Medium"}
            ],
            "annually": [
                {"task": "Full load generator test", "duration_min": 240, "criticality": "High"},
                {"task": "Oil and filter change", "duration_min": 120, "criticality": "High"},
                {"task": "Coolant replacement", "duration_min": 90, "criticality": "Medium"},
                {"task": "Professional inspection", "duration_min": 480, "criticality": "High"},
                {"task": "Comprehensive system report", "duration_min": 120, "criticality": "Medium"}
            ]
        }
        
        # Energy Management Algorithms
        self.energy_optimization_algorithms = {
            "load_shedding": "Shed non-essential loads during peak demand",
            "peak_shaving": "Use generator/battery during peak tariff periods",
            "demand_response": "Reduce load when grid requests",
            "load_balancing": "Balance loads across phases",
            "power_factor_correction": "Maintain power factor above 0.85 or 0.95"
        }
