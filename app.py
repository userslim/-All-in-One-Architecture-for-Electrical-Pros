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
        
        # Lighting design database (based on SS 531 / CIBSE / IES)
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
            }
        }
        
        # Socket outlet requirements (based on SS 638 and typical practice)
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
            "Hawker Centre / Market": {
                "density": "1 socket per stall (minimum 2)",
                "spacing": "At each stall location",
                "type": "13A BS 1363, IP66 weatherproof",
                "circuit_rating": "20A radial per stall",
                "max_sockets_per_circuit": 2,
                "special_requirements": ["Weatherproof covers", "Individual RCBO", "High temperature rating"]
            }
        }
        
        # Isolator requirements by room/equipment type
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
            }
        }
        
        # Fan selection database (for non-AC areas)
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
            }
        }
        
        # Ventilation requirements (air changes per hour - ACH)
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
            "Electrical Switchroom": {"ac_ach": 6, "non_ac_ach": 8, "notes": "Temperature control <35°C"}
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
            "Water Pump": 4.0
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

    # ==================== ROOM DESIGN FUNCTIONS ====================
    
    def calculate_lighting_design(self, room_type, length, width, height):
        """
        Calculate complete lighting design for a room
        """
        if room_type not in self.lighting_standards:
            return None
        
        area = length * width
        std = self.lighting_standards[room_type]
        
        # Calculate number of fittings using Lumen method
        recommended_lux = std["recommended_lux"]
        
        # Typical utilization factor (0.6-0.8) and maintenance factor (0.8)
        utilization_factor = 0.7
        maintenance_factor = 0.8
        
        # Total lumens required
        total_lumens = (area * recommended_lux) / (utilization_factor * maintenance_factor)
        
        # Number of fittings
        lumens_per_fitting = std["lumens_per_fitting"]
        num_fittings_raw = total_lumens / lumens_per_fitting
        
        # Round up to nearest integer and ensure even number for layout
        num_fittings = math.ceil(num_fittings_raw)
        if num_fittings % 2 != 0:
            num_fittings += 1
        
        # Calculate actual lux achieved
        actual_lumens = num_fittings * lumens_per_fitting
        actual_lux = (actual_lumens * utilization_factor * maintenance_factor) / area
        
        # Determine layout grid
        # Aim for spacing roughly 1.5x mounting height
        max_spacing = height * 1.5
        
        # Calculate fittings along length and width
        fittings_length = math.ceil(math.sqrt(num_fittings * (length / width)))
        fittings_width = math.ceil(num_fittings / fittings_length)
        
        # Adjust to get correct total
        while fittings_length * fittings_width < num_fittings:
            fittings_width += 1
        
        actual_fittings = fittings_length * fittings_width
        spacing_length = length / (fittings_length + 1)
        spacing_width = width / (fittings_width + 1)
        
        # Calculate load
        total_watts = num_fittings * std["watt_per_fitting"]
        watts_per_m2 = total_watts / area
        
        # Determine switch layout
        num_switches = max(1, math.ceil(fittings_length / 2))
        
        # Emergency lighting requirement
        emergency_required = std.get("emergency_required", "10%")
        if "100%" in emergency_required:
            emergency_fittings = num_fittings
        else:
            emergency_fittings = math.ceil(num_fittings * 0.1)
        
        return {
            "area": area,
            "recommended_lux": recommended_lux,
            "actual_lux": actual_lux,
            "fitting_type": std["fitting_type"],
            "lumens_per_fitting": lumens_per_fitting,
            "watt_per_fitting": std["watt_per_fitting"],
            "num_fittings": num_fittings,
            "actual_fittings": actual_fittings,
            "fittings_length": fittings_length,
            "fittings_width": fittings_width,
            "spacing_length": spacing_length,
            "spacing_width": spacing_width,
            "total_watts": total_watts,
            "watts_per_m2": watts_per_m2,
            "num_switches": num_switches,
            "emergency_fittings": emergency_fittings,
            "mounting_height": std["mounting_height"],
            "color_temp": std["color_temp"],
            "cri": std["cri_requirement"],
            "ip_rating": std.get("ip_rating", "IP20")
        }
    
    def calculate_socket_outlets(self, room_type, length, width):
        """
        Calculate number and placement of socket outlets
        """
        if room_type not in self.socket_outlet_standards:
            return None
        
        area = length * width
        perimeter = 2 * (length + width)
        std = self.socket_outlet_standards[room_type]
        
        # Calculate number based on density description
        if "per" in std["density"]:
            # Parse density like "1 per 5-8 m²"
            parts = std["density"].split("per")
            if len(parts) > 1:
                range_str = parts[1].strip().replace("m²", "").replace("²", "").strip()
                if "-" in range_str:
                    low, high = map(float, range_str.split("-"))
                    avg_density = (low + high) / 2
                else:
                    avg_density = float(range_str)
                
                # Number based on area
                num_sockets_raw = area / avg_density
                num_sockets = math.ceil(num_sockets_raw)
            else:
                num_sockets = 4  # Default
        else:
            num_sockets = 6  # Default
        
        # Calculate circuits required
        max_per_circuit = std["max_sockets_per_circuit"]
        num_circuits = math.ceil(num_sockets / max_per_circuit)
        
        # Calculate load
        load_per_socket = 300  # Watts (typical for general use)
        if "Industrial" in std["type"]:
            load_per_socket = 1000
        
        total_load = num_sockets * load_per_socket
        current_per_phase = total_load / (230 * 3)  # Assuming balanced across 3 phases
        
        # Socket placement recommendations
        if "spacing" in std:
            spacing_desc = std["spacing"]
            if "every" in spacing_desc.lower():
                # Parse spacing like "every 2.5-3m"
                import re
                numbers = re.findall(r"[\d.]+", spacing_desc)
                if numbers:
                    spacing = float(numbers[0])
                    sockets_per_wall = math.ceil(length / spacing) + math.ceil(width / spacing)
                    num_sockets = max(num_sockets, sockets_per_wall)
        
        return {
            "num_sockets": num_sockets,
            "socket_type": std["type"],
            "circuit_type": std["circuit_rating"],
            "num_circuits": num_circuits,
            "max_sockets_per_circuit": max_per_circuit,
            "total_load_watts": total_load,
            "total_load_kw": total_load / 1000,
            "current_per_phase": current_per_phase,
            "special_requirements": std["special_requirements"],
            "placement": f"Along walls at {spacing_desc if 'spacing' in std else 'standard spacing'}"
        }
    
    def get_isolator_requirements(self, room_type, equipment_list):
        """
        Get isolator requirements based on room type and equipment
        """
        isolators = []
        
        # General lighting isolator
        if "lighting" in equipment_list or "all" in equipment_list:
            isolators.append({
                "equipment": "General Lighting",
                "required": True,
                "type": "Light switch (local)",
                "location": "At room entrance",
                "details": self.isolator_requirements["General Lighting"]
            })
        
        # Socket outlet circuit isolator
        if "sockets" in equipment_list or "all" in equipment_list:
            isolators.append({
                "equipment": "Socket Outlets",
                "required": True,
                "type": "MCB in DB",
                "location": "Distribution board",
                "details": self.isolator_requirements["Socket Outlets"]
            })
        
        # Room-specific equipment
        room_isolators = {
            "Kitchen (Commercial)": ["Kitchen Equipment"],
            "Restaurant": ["Kitchen Equipment"],
            "Toilet / Bathroom": ["Water Heater"],
            "Plant Room": ["Pump / Motor"],
            "Generator Room": ["Generator"],
            "Electrical Switchroom": ["Switchboard"],
            "Hawker Centre": ["Stall (Hawker Centre)"],
            "Market": ["Stall (Hawker Centre)"]
        }
        
        if room_type in room_isolators:
            for equip in room_isolators[room_type]:
                if equip in self.isolator_requirements:
                    isolators.append({
                        "equipment": equip,
                        "required": True,
                        "type": self.isolator_requirements[equip]["type"],
                        "location": self.isolator_requirements[equip]["location"],
                        "details": self.isolator_requirements[equip]
                    })
        
        return isolators
    
    def calculate_fan_requirements(self, room_type, length, width, height, is_aircond=True):
        """
        Calculate fan requirements for non-aircond areas
        """
        area = length * width
        volume = area * height
        
        # Get ventilation requirements
        vent_req = self.ventilation_requirements.get(room_type, 
                    self.ventilation_requirements.get("Office", {"ac_ach": 6, "non_ac_ach": 8, "notes": ""}))
        
        if is_aircond:
            # For aircond areas, still need air movement for circulation
            ach_required = vent_req["ac_ach"]
            primary_purpose = "Air circulation"
        else:
            # For non-aircond, need ventilation for comfort
            ach_required = vent_req["non_ac_ach"]
            primary_purpose = "Ventilation and cooling"
        
        # Required airflow in CFM (Cubic Feet per Minute)
        # 1 ACH = Volume (m³) * 0.588 / 60 CFM (approx)
        required_cfm = volume * ach_required * 0.588
        
        # Select fan type based on room characteristics
        fan_recommendations = []
        
        # Check if HVLS fan is suitable (high ceiling, large area)
        if height >= 4 and area >= 150:
            # HVLS fan
            hvls_sizes = ["8ft", "10ft", "12ft", "16ft", "20ft"]
            for size in hvls_sizes:
                coverage = self.fan_database["High Volume Low Speed (HVLS)"]["coverage_area_m2"][size]
                if coverage >= area:
                    cfm = self.fan_database["High Volume Low Speed (HVLS)"]["airflow_cfm"][size]
                    power = self.fan_database["High Volume Low Speed (HVLS)"]["power_watts"][size]
                    num_fans = math.ceil(area / coverage)
                    fan_recommendations.append({
                        "type": "High Volume Low Speed (HVLS)",
                        "size": size,
                        "coverage_per_fan": coverage,
                        "num_fans": num_fans,
                        "cfm_per_fan": cfm,
                        "total_cfm": cfm * num_fans,
                        "power_watts": power * num_fans,
                        "mounting_height": self.fan_database["High Volume Low Speed (HVLS)"]["mounting_height"],
                        "noise_level": self.fan_database["High Volume Low Speed (HVLS)"]["noise_level"],
                        "speed_control": self.fan_database["High Volume Low Speed (HVLS)"]["speed_control"]
                    })
                    break
        
        # Check if commercial ceiling fans suitable
        if height <= 4 and area <= 500:
            fan_type = "Ceiling Fan (Commercial)" if area > 100 else "Ceiling Fan (Residential)"
            fan_data = self.fan_database[fan_type]
            coverage = fan_data["coverage_area_m2"]
            num_fans = math.ceil(area / coverage)
            
            # Select blade size based on room size
            if area <= 50:
                blade_size = fan_data["blade_diameter"][0]  # Smaller
            elif area <= 100:
                blade_size = fan_data["blade_diameter"][1] if len(fan_data["blade_diameter"]) > 1 else fan_data["blade_diameter"][0]
            else:
                blade_size = fan_data["blade_diameter"][-1]  # Larger
            
            fan_recommendations.append({
                "type": fan_type,
                "blade_size": blade_size,
                "coverage_per_fan": coverage,
                "num_fans": num_fans,
                "cfm_per_fan": fan_data["airflow_cfm"],
                "total_cfm": fan_data["airflow_cfm"] * num_fans,
                "power_watts": fan_data["power_watts"] * num_fans,
                "mounting_height": fan_data["mounting_height"],
                "noise_level": fan_data["noise_level"],
                "speed_control": fan_data["speed_control"]
            })
        
        # For kitchens, workshops, add wall mounted fans
        if "Kitchen" in room_type or "Workshop" in room_type:
            fan_type = "Wall Mounted Fan (Oscillating)"
            fan_data = self.fan_database[fan_type]
            
            # Select size based on area
            if area <= 50:
                blade_size = "18\" (450mm)"
                coverage = fan_data["coverage_area_m2"]["18\""]
                cfm = fan_data["airflow_cfm"]["18\""]
                power = fan_data["power_watts"]["18\""]
            elif area <= 100:
                blade_size = "24\" (600mm)"
                coverage = fan_data["coverage_area_m2"]["24\""]
                cfm = fan_data["airflow_cfm"]["24\""]
                power = fan_data["power_watts"]["24\""]
            else:
                blade_size = "30\" (750mm)"
                coverage = fan_data["coverage_area_m2"]["30\""]
                cfm = fan_data["airflow_cfm"]["30\""]
                power = fan_data["power_watts"]["30\""]
            
            num_fans = math.ceil(area / coverage)
            fan_recommendations.append({
                "type": fan_type,
                "blade_size": blade_size,
                "coverage_per_fan": coverage,
                "num_fans": num_fans,
                "cfm_per_fan": cfm,
                "total_cfm": cfm * num_fans,
                "power_watts": power * num_fans,
                "mounting_height": fan_data["mounting_height"],
                "noise_level": fan_data["noise_level"],
                "speed_control": fan_data["speed_control"],
                "note": "For targeted air movement"
            })
        
        # Add exhaust fans for rooms requiring ventilation
        if "Toilet" in room_type or "Kitchen" in room_type or "Plant Room" in room_type or "Battery" in room_type:
            fan_type = "Exhaust Fan (Wall/Ceiling)"
            fan_data = self.fan_database[fan_type]
            
            # Calculate required exhaust CFM based on ACH
            required_exhaust_cfm = volume * vent_req["non_ac_ach"] * 0.588
            
            # Select size
            if required_exhaust_cfm <= 200:
                blade_size = "8\" (200mm)"
                cfm = fan_data["airflow_cfm"]["8\""]
                power = fan_data["power_watts"]["8\""]
            elif required_exhaust_cfm <= 400:
                blade_size = "10\" (250mm)"
                cfm = fan_data["airflow_cfm"]["10\""]
                power = fan_data["power_watts"]["10\""]
            elif required_exhaust_cfm <= 700:
                blade_size = "12\" (300mm)"
                cfm = fan_data["airflow_cfm"]["12\""]
                power = fan_data["power_watts"]["12\""]
            else:
                blade_size = "Multiple 12\" units"
                num_exhaust = math.ceil(required_exhaust_cfm / 800)
                cfm = 800
                power = 80 * num_exhaust
            
            if blade_size == "Multiple 12\" units":
                fan_recommendations.append({
                    "type": fan_type,
                    "blade_size": blade_size,
                    "num_fans": num_exhaust,
                    "total_cfm": cfm * num_exhaust,
                    "power_watts": power,
                    "purpose": fan_data["purpose"],
                    "installation": fan_data["installation"],
                    "note": f"Required for {ach_required} air changes per hour"
                })
            else:
                fan_recommendations.append({
                    "type": fan_type,
                    "blade_size": blade_size,
                    "num_fans": 1,
                    "cfm_per_fan": cfm,
                    "total_cfm": cfm,
                    "power_watts": power,
                    "purpose": fan_data["purpose"],
                    "installation": fan_data["installation"],
                    "note": f"Required for {ach_required} air changes per hour"
                })
        
        return {
            "area": area,
            "volume": volume,
            "is_aircond": is_aircond,
            "ach_required": ach_required,
            "required_cfm": required_cfm,
            "primary_purpose": primary_purpose,
            "fan_recommendations": fan_recommendations,
            "total_power_watts": sum(f["power_watts"] for f in fan_recommendations) if fan_recommendations else 0,
            "notes": vent_req["notes"]
        }
    
    # ==================== EXISTING FUNCTIONS ====================
    
    def get_at_af(self, ib):
        at = next((x for x in self.standard_trips if x >= ib), 4000)
        af = next((x for x in self.standard_frames if x >= at), 4000)
        return at, af
    
    def calculate_voltage_drop(self, cable_size, current, length, pf=0.85):
        if cable_size not in self.cable_impedance:
            return None, None
        
        impedance = self.cable_impedance[cable_size]
        sin_phi = math.sqrt(1 - pf**2)
        v_drop_per_km = math.sqrt(3) * current * (impedance["r"] * pf + impedance["x"] * sin_phi)
        v_drop = v_drop_per_km * length / 1000
        v_drop_percent = (v_drop / 400) * 100
        
        return v_drop, v_drop_percent
    
    def select_cable_with_vd(self, ib, length, pf=0.85, max_vd_percent=4):
        suitable_cables = []
        for size, iz in self.cable_db.items():
            if iz >= ib * 1.25:
                vd, vd_percent = self.calculate_voltage_drop(size, ib, length, pf)
                if vd_percent and vd_percent <= max_vd_percent:
                    suitable_cables.append({
                        "size": size,
                        "iz": iz,
                        "vd": vd,
                        "vd_percent": vd_percent
                    })
        
        if suitable_cables:
            return min(suitable_cables, key=lambda x: x["size"])
        else:
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
    
    def calculate_cable_tray_size(self, cables, tray_depth=50, tray_type="perforated", spare_capacity=0.25):
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
                    "area": area
                })
        
        total_area_with_spare = total_area * (1 + spare_capacity)
        fill_factor = self.tray_fill_factors.get(tray_type, 0.4)
        required_width = total_area_with_spare / (tray_depth * fill_factor)
        selected_width = next((w for w in self.standard_tray_sizes if w >= required_width), 
                              self.standard_tray_sizes[-1])
        actual_fill = (total_area / (selected_width * tray_depth)) * 100
        
        return {
            "total_cable_area": total_area,
            "total_area_with_spare": total_area_with_spare,
            "required_width": required_width,
            "selected_width": selected_width,
            "tray_depth": tray_depth,
            "tray_type": tray_type,
            "fill_factor": fill_factor,
            "actual_fill_percentage": actual_fill,
            "cable_details": cable_details,
            "spare_capacity": spare_capacity * 100
        }
    
    def calculate_generator_size(self, essential_loads, fire_loads, largest_motor_starting_kva):
        total_running_kva = sum(essential_loads) + sum(fire_loads)
        other_running_kva = total_running_kva - largest_motor_starting_kva
        starting_scenario_kva = other_running_kva + largest_motor_starting_kva
        required_gen_size = max(total_running_kva, starting_scenario_kva) * 1.2
        
        standard_gen_sizes = [20, 30, 45, 60, 80, 100, 125, 150, 200, 250, 300, 400, 500, 630, 750, 800, 1000, 1250, 1500, 2000]
        recommended_gen = next((x for x in standard_gen_sizes if x >= required_gen_size), required_gen_size)
        
        return required_gen_size, recommended_gen, total_running_kva, starting_scenario_kva
    
    def calculate_earth_pits(self, has_fuel_tank=True, soil_condition="Normal", building_area=0, protection_level="Level III"):
        earth_pits = {
            "generator_body": 2,
            "fuel_tank": 1 if has_fuel_tank else 0,
            "lightning_protection": 0,
            "total_recommended": 0
        }
        
        if soil_condition == "Poor (High Resistance)":
            earth_pits["generator_body"] = 3
        
        if building_area > 0:
            if building_area <= 500:
                earth_pits["lightning_protection"] = 2
            elif building_area <= 2000:
                earth_pits["lightning_protection"] = 4
            elif building_area <= 5000:
                earth_pits["lightning_protection"] = 6
            else:
                earth_pits["lightning_protection"] = 8 + math.ceil((building_area - 5000) / 2000)
            
            level_multiplier = {
                "Level I": 1.5,
                "Level II": 1.2,
                "Level III": 1.0,
                "Level IV": 0.8
            }
            earth_pits["lightning_protection"] = math.ceil(earth_pits["lightning_protection"] * level_multiplier[protection_level])
        
        earth_pits["total_recommended"] = earth_pits["generator_body"] + earth_pits["fuel_tank"] + earth_pits["lightning_protection"]
        
        return earth_pits
    
    def calculate_lightning_protection(self, building_length, building_width, building_height, protection_level="Level III", roof_type="Flat"):
        building_area = building_length * building_width
        perimeter = 2 * (building_length + building_width)
        
        spacing = self.air_terminal_spacing[protection_level]
        
        if building_height < 10:
            height_category = "low"
        elif building_height < 20:
            height_category = "medium"
        else:
            height_category = "high"
        
        terminal_spacing = spacing[height_category]
        
        terminals_length = math.ceil(building_length / terminal_spacing) + 1
        terminals_width = math.ceil(building_width / terminal_spacing) + 1
        
        if roof_type == "Flat":
            num_air_terminals = terminals_length * terminals_width
        else:
            num_air_terminals = terminals_length * 2 + terminals_width
        
        num_down_conductors = max(2, math.ceil(perimeter / 20))
        num_test_joints = num_down_conductors
        
        roof_conductor_length = (terminals_length - 1) * building_width + (terminals_width - 1) * building_length
        down_conductor_length = num_down_conductors * building_height * 2
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
        emergency_lights = {
            "escape_route_lights": int(total_lights * 0.2 * (escape_route_lights_percent / 100)),
            "general_area_lights": int(total_lights * 0.8 * (general_area_percent / 100)),
            "exit_signs": int(total_lights * 0.1)
        }
        
        emergency_lights["total_emergency_lights"] = emergency_lights["escape_route_lights"] + emergency_lights["general_area_lights"] + emergency_lights["exit_signs"]
        emergency_lights["emergency_load_watts"] = emergency_lights["total_emergency_lights"] * 10
        
        return emergency_lights

# --- UI SETUP ---
st.set_page_config(page_title="SG Electrical Design Pro - Complete Room Design", layout="wide")
engine = SGProEngine()

st.title("⚡ Singapore Electrical Design Professional")
st.subheader("Complete Room-by-Room Design Guide for Installers & Engineers")
st.markdown("**Compliant with SS 638, SS 531 (Lighting), SS 553 (Ventilation), SP Group & BCA Requirements**")

# Sidebar
with st.sidebar:
    st.header("📋 Quick Reference")
    st.info("**SS 638:** Electrical Installations")
    st.info("**SS 531:** Lighting & Illumination")
    st.info("**SS 553:** Ventilation & Air Conditioning")
    
    st.divider()
    
    st.header("🏢 Building Information")
    building_length = st.number_input("Building Length (m)", min_value=1.0, value=50.0)
    building_width = st.number_input("Building Width (m)", min_value=1.0, value=30.0)
    building_height = st.number_input("Building Height (m)", min_value=1.0, value=15.0)
    roof_type = st.selectbox("Roof Type", ["Flat", "Pitched"])
    protection_level = st.selectbox("Lightning Protection Level", 
                                   ["Level I", "Level II", "Level III", "Level IV"], 
                                   index=2)

# Create main tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏢 ROOM DESIGN (Lighting, Sockets, Fans)",
    "📊 Main MSB Design",
    "🔌 Cable & Containment",
    "🔄 Generator Systems",
    "⚡ Lightning Protection",
    "📋 Checklists"
])

# ==================== TAB 1: COMPREHENSIVE ROOM DESIGN ====================
with tab1:
    st.header("🏢 Complete Room Electrical Design")
    st.write("Design lighting, socket outlets, isolators, and ventilation fans for any room")
    st.write("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("1️⃣ Room Information")
        
        # Room selection
        room_types = list(engine.lighting_standards.keys())
        selected_room = st.selectbox("Select Room Type", room_types, key="room_type_main")
        
        # Room dimensions
        st.write("**Room Dimensions:**")
        col_dim1, col_dim2, col_dim3 = st.columns(3)
        with col_dim1:
            room_length = st.number_input("Length (m)", min_value=1.0, value=10.0, key="room_length")
        with col_dim2:
            room_width = st.number_input("Width (m)", min_value=1.0, value=8.0, key="room_width")
        with col_dim3:
            room_height = st.number_input("Height (m)", min_value=2.0, value=3.0, key="room_height")
        
        # Air conditioning status
        is_aircond = st.radio("Air Conditioning Status", 
                             ["Air Conditioned", "Non Air Conditioned (Fan Only)"],
                             index=0)
        
        # Additional equipment
        st.write("**Equipment Present:**")
        has_lighting = st.checkbox("General Lighting", value=True)
        has_sockets = st.checkbox("Socket Outlets", value=True)
        has_special_equip = st.checkbox("Special Equipment (Kitchen, Pumps, etc.)")
        
        if has_special_equip:
            special_equip = st.multiselect("Select Equipment Types",
                                          ["Kitchen Equipment", "Water Heater", "Pump / Motor", 
                                           "Air Conditioner", "Industrial Machine"])
        else:
            special_equip = []
        
        if st.button("Calculate Room Design", type="primary", use_container_width=True):
            # Prepare equipment list
            equipment_list = []
            if has_lighting:
                equipment_list.append("lighting")
            if has_sockets:
                equipment_list.append("sockets")
            equipment_list.extend([e.lower() for e in special_equip])
            
            with col2:
                st.subheader("2️⃣ DESIGN RESULTS")
                
                # ===== LIGHTING DESIGN =====
                if has_lighting:
                    st.write("### 💡 Lighting Design")
                    lighting = engine.calculate_lighting_design(selected_room, room_length, room_width, room_height)
                    
                    if lighting:
                        col_light1, col_light2, col_light3 = st.columns(3)
                        with col_light1:
                            st.metric("Area", f"{lighting['area']:.1f} m²")
                        with col_light2:
                            st.metric("Required Lux", f"{lighting['recommended_lux']} lx")
                        with col_light3:
                            st.metric("Achieved Lux", f"{lighting['actual_lux']:.0f} lx")
                        
                        st.write(f"**Fitting Type:** {lighting['fitting_type']}")
                        st.write(f"**Number of Fittings:** {lighting['num_fittings']} nos")
                        st.write(f"**Layout:** {lighting['fittings_length']} rows × {lighting['fittings_width']} columns")
                        st.write(f"**Spacing:** {lighting['spacing_length']:.1f}m (L) × {lighting['spacing_width']:.1f}m (W)")
                        st.write(f"**Total Load:** {lighting['total_watts']}W ({lighting['watts_per_m2']:.1f} W/m²)")
                        st.write(f"**Switches Required:** {lighting['num_switches']} nos (at entrance)")
                        st.write(f"**Emergency Fittings:** {lighting['emergency_fittings']} nos")
                        st.write(f"**Color Temperature:** {lighting['color_temp']}")
                        st.write(f"**CRI:** {lighting['cri']}")
                        st.write(f"**IP Rating:** {lighting['ip_rating']}")
                        
                        # Isolator for lighting
                        st.write("**Isolator Requirement:** Light switch at entrance (required)")
                    
                    st.divider()
                
                # ===== SOCKET OUTLET DESIGN =====
                if has_sockets:
                    st.write("### 🔌 Socket Outlet Design")
                    sockets = engine.calculate_socket_outlets(selected_room, room_length, room_width)
                    
                    if sockets:
                        st.write(f"**Number of Sockets:** {sockets['num_sockets']} nos")
                        st.write(f"**Socket Type:** {sockets['socket_type']}")
                        st.write(f"**Circuit Type:** {sockets['circuit_type']}")
                        st.write(f"**Number of Circuits:** {sockets['num_circuits']} (max {sockets['max_sockets_per_circuit']} per circuit)")
                        st.write(f"**Total Load:** {sockets['total_load_kw']:.2f} kW ({sockets['current_per_phase']:.1f} A per phase)")
                        st.write(f"**Placement:** {sockets['placement']}")
                        
                        st.write("**Special Requirements:**")
                        for req in sockets['special_requirements']:
                            st.write(f"- {req}")
                        
                        # Isolator for sockets
                        st.write("**Isolator Requirement:** MCB in Distribution Board")
                    
                    st.divider()
                
                # ===== ISOLATOR REQUIREMENTS =====
                st.write("### 🔒 Isolator Requirements")
                isolators = engine.get_isolator_requirements(selected_room, equipment_list)
                
                if isolators:
                    for iso in isolators:
                        st.write(f"**{iso['equipment']}:**")
                        st.write(f"- Type: {iso['type']}")
                        st.write(f"- Location: {iso['location']}")
                        st.write(f"- Purpose: {iso['details']['purpose']}")
                else:
                    st.write("No specific isolators required beyond standard switches")
                
                st.divider()
                
                # ===== FAN & VENTILATION DESIGN =====
                ac_status = "Air Conditioned" in is_aircond
                st.write(f"### {'🌀' if not ac_status else '❄️'} Ventilation & Fan Design")
                st.write(f"**Status:** {'Air Conditioned' if ac_status else 'Non Air Conditioned'}")
                
                fans = engine.calculate_fan_requirements(selected_room, room_length, room_width, room_height, ac_status)
                
                if fans:
                    st.write(f"**Room Volume:** {fans['volume']:.1f} m³")
                    st.write(f"**Required Air Changes:** {fans['ach_required']} ACH")
                    st.write(f"**Required Airflow:** {fans['required_cfm']:.0f} CFM")
                    st.write(f"**Purpose:** {fans['primary_purpose']}")
                    
                    if fans['fan_recommendations']:
                        st.write("**Fan Recommendations:**")
                        for fan in fans['fan_recommendations']:
                            with st.expander(f"**{fan['type']}**"):
                                if 'blade_size' in fan:
                                    st.write(f"- Blade Size: {fan['blade_size']}")
                                if 'size' in fan:
                                    st.write(f"- Size: {fan['size']}")
                                st.write(f"- Quantity: {fan['num_fans']} units")
                                if 'cfm_per_fan' in fan:
                                    st.write(f"- Airflow per fan: {fan['cfm_per_fan']} CFM")
                                st.write(f"- Total Airflow: {fan['total_cfm']} CFM")
                                st.write(f"- Total Power: {fan['power_watts']}W")
                                if 'mounting_height' in fan:
                                    st.write(f"- Mounting Height: {fan['mounting_height']}")
                                if 'noise_level' in fan:
                                    st.write(f"- Noise Level: {fan['noise_level']}")
                                if 'speed_control' in fan:
                                    st.write(f"- Speed Control: {fan['speed_control']}")
                                if 'note' in fan:
                                    st.write(f"- Note: {fan['note']}")
                    
                    st.write(f"**Total Fan Power:** {fans['total_power_watts']}W")
                    st.write(f"**Notes:** {fans['notes']}")
                    
                    # Fan isolator requirements
                    if fans['total_power_watts'] > 0:
                        st.write("**Isolator Requirements:**")
                        for fan in fans['fan_recommendations']:
                            if "HVLS" in fan['type'] or "Wall Mounted" in fan['type']:
                                st.write(f"- {fan['type']}: Local isolator with lockable handle required")
                            else:
                                st.write(f"- {fan['type']}: Wall switch/speed controller only")
                
                st.divider()
                
                # ===== SUMMARY =====
                st.success("### 📋 Summary")
                
                total_power = 0
                if has_lighting and lighting:
                    total_power += lighting['total_watts']
                if has_sockets and sockets:
                    total_power += sockets['total_load_watts']
                if fans and 'total_power_watts' in fans:
                    total_power += fans['total_power_watts']
                
                st.write(f"**Total Electrical Load:** {total_power/1000:.2f} kW")
                st.write(f"**Total Current (at 230V):** {total_power/230:.1f} A")
                
                # Recommend circuit breaker
                if total_power > 0:
                    current = total_power / 230
                    if current <= 20:
                        st.write("**Recommended Circuit:** 20A Radial Circuit")
                    elif current <= 32:
                        st.write("**Recommended Circuit:** 32A Radial Circuit")
                    else:
                        st.write(f"**Recommended:** Multiple Circuits ({math.ceil(current/20)} × 20A circuits)")
                
                # Download design report option
                st.download_button(
                    label="📥 Download Design Report",
                    data=f"""ROOM ELECTRICAL DESIGN REPORT
Room Type: {selected_room}
Dimensions: {room_length}m × {room_width}m × {room_height}m
Area: {room_length * room_width:.1f} m²

LIGHTING DESIGN:
- Fittings: {lighting['num_fittings'] if has_lighting else 'N/A'} nos
- Lux Level: {lighting['actual_lux']:.0f} lx
- Power: {lighting['total_watts'] if has_lighting else 0}W

SOCKET OUTLETS:
- Quantity: {sockets['num_sockets'] if has_sockets else 'N/A'} nos
- Load: {sockets['total_load_kw'] if has_sockets else 0}kW

FAN REQUIREMENTS:
- Type: {fans['fan_recommendations'][0]['type'] if fans['fan_recommendations'] else 'None'}
- Quantity: {fans['fan_recommendations'][0]['num_fans'] if fans['fan_recommendations'] else 0}
- Power: {fans['total_power_watts']}W

TOTAL LOAD: {total_power/1000:.2f} kW
""",
                    file_name=f"{selected_room}_design_report.txt",
                    mime="text/plain"
                )

# ==================== TAB 2: MAIN MSB DESIGN ====================
with tab2:
    st.header("📊 Main Switchboard (MSB) Design")
    st.write("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Load Parameters")
        load_kw = st.number_input("Design Load (kW)", value=100.0, key="msb_load")
        pf = st.slider("Power Factor", 0.7, 1.0, 0.85, key="msb_pf")
        cable_length = st.number_input("Cable Length (m)", min_value=1.0, value=50.0, key="msb_cable_length")
        max_vd = st.slider("Max Voltage Drop %", 1.0, 8.0, 4.0, 0.5, key="msb_vd")
        num_feeder = st.number_input("Number of Outgoing Feeders", min_value=1, value=5, key="msb_feeders")
        
        ib = (load_kw * 1000) / (math.sqrt(3) * 400 * pf)
        
        if st.button("Calculate MSB", type="primary"):
            with col2:
                st.subheader("Results")
                
                # Breaker selection
                at, af = engine.get_at_af(ib)
                b_type = "ACB" if af >= 800 else "MCCB" if af > 63 else "MCB"
                
                st.metric("Design Current (Ib)", f"{ib:.2f} A")
                st.success(f"**Incomer:** {at}AT / {af}AF {b_type}")
                
                # Cable selection
                cable = engine.select_cable_with_vd(ib, cable_length, pf, max_vd)
                
                if "error" in cable:
                    st.error(cable["error"])
                else:
                    st.write(f"**Cable:** {cable['size']} mm² Cu/XLPE/SWA/PVC")
                    st.write(f"**Current Capacity:** {cable['iz']} A")
                    vd_color = "🟢" if cable['vd_percent'] <= max_vd else "🔴"
                    st.write(f"**Voltage Drop:** {vd_color} {cable['vd']:.2f}V ({cable['vd_percent']:.2f}%)")
                    
                    if "warning" in cable:
                        st.warning(cable["warning"])
                
                # MSB physical size
                base_width = 800 if b_type == "ACB" else 600
                total_width = (base_width + num_feeder * 400) * 1.2
                st.write(f"**Estimated MSB Width:** {total_width:.0f} mm")

# ==================== TAB 3: CABLE & CONTAINMENT ====================
with tab3:
    st.header("🔌 Cable & Containment Sizing")
    st.write("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Cable Tray Sizing")
        
        available_cables = list(engine.cable_db.keys())
        num_cables = st.number_input("Number of different cable sizes", min_value=1, value=3, key="tray_num")
        
        cables_in_tray = []
        for i in range(num_cables):
            col_size, col_qty = st.columns(2)
            with col_size:
                cable_size = st.selectbox(f"Cable {i+1} size", available_cables, key=f"tray_cable_{i}")
            with col_qty:
                qty = st.number_input(f"Quantity", min_value=1, value=3, key=f"tray_qty_{i}")
            
            for _ in range(qty):
                cables_in_tray.append(cable_size)
        
        tray_depth = st.selectbox("Tray depth (mm)", [50, 75, 100, 150], key="tray_depth")
        tray_type = st.selectbox("Tray type", ["perforated", "ladder", "solid", "wire_mesh"], key="tray_type")
        spare = st.slider("Spare capacity %", 0, 50, 25, key="tray_spare") / 100
        
        if st.button("Calculate Tray", type="primary"):
            result = engine.calculate_cable_tray_size(cables_in_tray, tray_depth, tray_type, spare)
            
            with col2:
                st.subheader("Results")
                st.write(f"**Total Cable Area:** {result['total_cable_area']:.0f} mm²")
                st.write(f"**With {spare*100:.0f}% Spare:** {result['total_area_with_spare']:.0f} mm²")
                st.write(f"**Required Width:** {result['required_width']:.0f} mm")
                st.write(f"**Selected Tray:** {result['selected_width']} mm wide")
                st.write(f"**Actual Fill:** {result['actual_fill_percentage']:.1f}%")
                
                if result['actual_fill_percentage'] <= result['fill_factor'] * 100:
                    st.success("✅ Tray size is adequate")
                else:
                    st.error("⚠️ Tray is overfilled - select larger size")

# ==================== TAB 4: GENERATOR SYSTEMS ====================
with tab4:
    st.header("🔄 Generator Sizing")
    st.write("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Essential Loads")
        num_lifts = st.number_input("Number of Lifts", min_value=0, value=2, key="gen_lifts")
        lift_loads = []
        lift_starting = []
        
        for i in range(num_lifts):
            lift_kw = st.number_input(f"Lift {i+1} Motor (kW)", value=10.0, key=f"gen_lift_{i}_kw")
            lift_pf = st.slider(f"Lift {i+1} PF", 0.7, 1.0, 0.85, key=f"gen_lift_{i}_pf")
            
            running = (lift_kw * 1000) / (math.sqrt(3) * 400 * lift_pf) / 1000
            starting = running * 2.5  # Typical multiplier
            
            lift_loads.append(running)
            lift_starting.append(starting)
            st.caption(f"Running: {running:.1f} kVA | Starting: {starting:.1f} kVA")
    
    with col2:
        st.subheader("Fire Loads")
        has_pump = st.checkbox("Include Fire Pump", value=True, key="gen_pump")
        fire_loads = []
        fire_starting = []
        
        if has_pump:
            pump_kw = st.number_input("Fire Pump Motor (kW)", value=30.0, key="gen_pump_kw")
            pump_pf = st.slider("Fire Pump PF", 0.7, 1.0, 0.85, key="gen_pump_pf")
            pump_type = st.selectbox("Starting Type", 
                                    ["Direct Online", "Star-Delta", "Soft Starter"], key="gen_pump_type")
            
            multiplier = {"Direct Online": 6.0, "Star-Delta": 3.5, "Soft Starter": 2.5}[pump_type]
            running = (pump_kw * 1000) / (math.sqrt(3) * 400 * pump_pf) / 1000
            starting = running * multiplier
            
            fire_loads.append(running)
            fire_starting.append(starting)
            st.caption(f"Running: {running:.1f} kVA | Starting: {starting:.1f} kVA")
    
    if st.button("Calculate Generator", type="primary"):
        all_starting = lift_starting + fire_starting
        largest = max(all_starting) if all_starting else 0
        
        required, recommended, running, starting = engine.calculate_generator_size(
            lift_loads, fire_loads, largest
        )
        
        st.success(f"✅ **Recommended Generator:** {recommended:.0f} kVA (Prime Rating)")
        st.info(f"Running Load: {running:.1f} kVA | Starting Load: {starting:.1f} kVA")

# ==================== TAB 5: LIGHTNING PROTECTION ====================
with tab5:
    st.header("⚡ Lightning Protection System")
    st.write("---")
    
    if st.button("Calculate Lightning Protection", type="primary"):
        lp = engine.calculate_lightning_protection(
            building_length, building_width, building_height, protection_level, roof_type
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Building Parameters")
            st.write(f"Area: {lp['building_area']:.0f} m²")
            st.write(f"Perimeter: {lp['perimeter']:.0f} m")
            st.write(f"Protection Level: {protection_level}")
            st.write(f"Terminal Spacing: {lp['terminal_spacing']} m")
        
        with col2:
            st.subheader("Bill of Materials")
            st.write(f"Air Terminals: {lp['num_air_terminals']} nos")
            st.write(f"Down Conductors: {lp['num_down_conductors']} nos")
            st.write(f"Test Joints: {lp['num_test_joints']} nos")
            st.write(f"Total Conductor: {lp['total_conductor_length']:.0f} m")

# ==================== TAB 6: CHECKLISTS ====================
with tab6:
    st.header("📋 Project Checklists")
    st.write("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📐 DESIGN CHECKLIST")
        st.checkbox("Load assessment completed")
        st.checkbox("Cable sizing with voltage drop")
        st.checkbox("Protection coordination study")
        st.checkbox("Earthing system designed")
        st.checkbox("Lightning protection designed")
        st.checkbox("Emergency lighting designed")
        st.checkbox("Room-by-room load calculated")
        st.checkbox("Fan/ventilation requirements")
    
    with col2:
        st.subheader("🔧 INSTALLATION CHECKLIST")
        st.checkbox("Site inspection done")
        st.checkbox("Material delivery verified")
        st.checkbox("Cable routes marked")
        st.checkbox("Earth pits installed")
        st.checkbox("Lightning protection installed")
        st.checkbox("Testing completed")
        st.checkbox("As-built drawings prepared")
        st.checkbox("O&M manuals submitted")

# Footer
st.divider()
st.caption("© Singapore Electrical Design Professional - Complete Room Design Tool | Compliant with SS 638, SS 531, SS 553")
