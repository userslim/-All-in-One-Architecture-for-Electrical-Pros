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
        
        # Cable diameter database (approximate overall diameter in mm)
        self.cable_diameters = {
            1.5: 12, 2.5: 13, 4: 14, 6: 15, 10: 17, 16: 19, 25: 22, 35: 24,
            50: 27, 70: 30, 95: 33, 120: 36, 150: 39, 185: 42, 240: 46, 300: 50,
            400: 55, 500: 60, 630: 65
        }
        
        # Cable resistance and reactance (Ohms/km) for voltage drop calculation
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
        
        # Cable tray sizing factors (based on SS 638 / IEC 61537)
        self.tray_fill_factors = {
            "perforated": 0.4,  # 40% maximum fill
            "ladder": 0.4,      # 40% maximum fill
            "solid": 0.3,       # 30% maximum fill
            "wire_mesh": 0.35   # 35% maximum fill
        }
        
        # Standard tray sizes (width in mm)
        self.standard_tray_sizes = [50, 100, 150, 200, 300, 400, 450, 500, 600, 750, 900]
        
        # Room electrical load database (based on SS 638 and typical Singapore practices)
        self.room_load_database = {
            "Office Areas": {
                "description": "General office spaces",
                "lighting_load": 15,  # W/m²
                "socket_load": 25,     # W/m² (general purpose outlets)
                "equipment_load": 30,   # W/m² (computers, printers, etc.)
                "ac_load": 80,          # W/m² (air conditioning)
                "diversity_factor": 0.7,
                "typical_equipment": ["LED lights", "13A sockets", "Computers", "Printers", "Water coolers"]
            },
            "Meeting Rooms": {
                "description": "Conference and meeting areas",
                "lighting_load": 20,
                "socket_load": 30,
                "equipment_load": 50,   # Projectors, AV equipment
                "ac_load": 100,
                "diversity_factor": 0.8,
                "typical_equipment": ["AV systems", "Projectors", "Video conferencing", "Laptop charging"]
            },
            "IT Server Room": {
                "description": "Data center / server room",
                "lighting_load": 10,
                "socket_load": 15,
                "equipment_load": 500,  # Servers, networking equipment
                "ac_load": 400,          # Precision cooling
                "diversity_factor": 1.0,
                "typical_equipment": ["Servers", "Racks", "UPS", "PDU", "Network switches"],
                "special_requirements": ["UPS backup", "Generator essential", "Dedicated AC", "Fire suppression"]
            },
            "Electrical Switchroom": {
                "description": "MSB/MDB/DB locations",
                "lighting_load": 10,
                "socket_load": 10,
                "equipment_load": 5,      # Control panels, etc.
                "ac_load": 50,            # Cooling for switchgear
                "diversity_factor": 0.9,
                "typical_equipment": ["Switchboards", "Control panels", "MCC", "Capacitor banks"],
                "special_requirements": ["Ventilation", "Emergency lighting", "Fire detection"]
            },
            "Generator Room": {
                "description": "Generator set location",
                "lighting_load": 15,
                "socket_load": 10,
                "equipment_load": 0,      # Generator load calculated separately
                "ac_load": 30,             # Ventilation fans
                "diversity_factor": 0.8,
                "typical_equipment": ["Generator set", "ATS", "Fuel tank", "Battery charger"],
                "special_requirements": ["Exhaust extraction", "Fuel leak detection", "Sound attenuation"]
            },
            "Pump Room": {
                "description": "Fire pump / water pump room",
                "lighting_load": 10,
                "socket_load": 10,
                "equipment_load": 0,      # Pump loads calculated separately
                "ac_load": 20,             # Ventilation
                "diversity_factor": 0.7,
                "typical_equipment": ["Fire pumps", "Jockey pumps", "Control panels", "Flow switches"],
                "special_requirements": ["Fire rated wiring", "Emergency stop", "Float switches"]
            },
            "Car Park": {
                "description": "Basement or multi-storey carpark",
                "lighting_load": 5,        # W/m² (LED lighting)
                "socket_load": 2,           # Car park sockets
                "equipment_load": 3,        # Ventilation fans, barriers
                "ac_load": 0,               # Natural ventilation typically
                "diversity_factor": 0.6,
                "typical_equipment": ["LED lights", "Ventilation fans", "Car park barriers", "EV chargers"],
                "special_requirements": ["CO monitoring", "Ventilation control", "Emergency lighting"]
            },
            "Corridor / Staircase": {
                "description": "Common areas and escape routes",
                "lighting_load": 8,
                "socket_load": 1,
                "equipment_load": 0,
                "ac_load": 0,
                "diversity_factor": 1.0,
                "typical_equipment": ["Emergency lights", "Exit signs"],
                "special_requirements": ["100% emergency lighting backup", "Fire rated"]
            },
            "Toilet / Pantry": {
                "description": "Washrooms and kitchenettes",
                "lighting_load": 12,
                "socket_load": 10,
                "equipment_load": 15,      # Water heaters, coffee machines
                "ac_load": 20,              # Exhaust fans
                "diversity_factor": 0.5,
                "typical_equipment": ["Exhaust fans", "Water heaters", "Hand dryers", "Kitchen appliances"]
            },
            "Loading Bay": {
                "description": "Goods delivery area",
                "lighting_load": 10,
                "socket_load": 10,
                "equipment_load": 20,      # Dock levellers, doors
                "ac_load": 0,
                "diversity_factor": 0.6,
                "typical_equipment": ["Dock levellers", "Roller shutters", "Charging points"]
            },
            "FAHU / AC Plant Room": {
                "description": "Air handling units and chiller plant",
                "lighting_load": 10,
                "socket_load": 10,
                "equipment_load": 0,      # HVAC loads calculated separately
                "ac_load": 0,
                "diversity_factor": 0.8,
                "typical_equipment": ["AHU", "Chillers", "Pumps", "Control panels"],
                "special_requirements": ["VFDs", "BMS connection", "Maintenance isolation"]
            }
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
            "Water Pump": 4.0
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

    # ==================== EDUCATIONAL NOTES FOR INSTALLERS ====================
    def get_installer_notes(self, topic):
        """Provide educational notes for installers and junior engineers"""
        notes = {
            "cable_sizing": """
            **📚 CABLE SIZING FOR INSTALLERS (SS 638):**
            
            **Step-by-Step Guide:**
            1. **Calculate Design Current (Ib):** 
               - Formula: Ib = Power (kW) × 1000 / (√3 × 400V × Power Factor)
               - Example: 100kW motor at 0.85pf = 100×1000/(1.732×400×0.85) = 170A
            
            2. **Select Cable Size Based on Current:**
               - Check Table 4E4A in SS 638 for Cu/XLPE cables
               - Cable must have Iz ≥ Ib × 1.25 (for continuous loads)
               - Example: For 170A, need cable with Iz ≥ 212.5A → 70mm² (Iz=255A)
            
            3. **Check Voltage Drop:**
               - Maximum allowed: 4% for main runs, 6.5% for final circuits
               - Voltage drop increases with length and current
               - If voltage drop > limit, go up one cable size
            
            4. **Check Cable Installation Method:**
               - Method E (in free air) vs Method C (in conduit)
               - Derating factors for grouping, ambient temperature
               - Use correction factors from SS 638 tables
            
            **⚠️ Common Installation Mistakes:**
            - Using cable based only on current, ignoring voltage drop
            - Not applying derating factors for grouped cables
            - Incorrect cable gland selection for armor type
            - Poor termination causing hot spots
            """,
            
            "cable_containment": """
            **📚 CABLE CONTAINMENT SIZING (SS 638 / IEC 61537):**
            
            **Cable Tray Types:**
            1. **Perforated Tray:** Good ventilation, max fill 40%
            2. **Ladder Tray:** Best for large cables, max fill 40%
            3. **Solid Tray:** Dust protection, max fill 30%
            4. **Wire Mesh:** Flexible for small cables, max fill 35%
            
            **Sizing Formula:**
            ```
            Required Width = (Sum of cable cross-sectional areas) / (Tray Depth × Fill Factor)
            ```
            
            **Step-by-Step Sizing:**
            1. Calculate cross-sectional area of each cable (π × (diameter/2)²)
            2. Sum all cable areas
            3. Divide by fill factor (0.4 for perforated)
            4. Divide by tray depth (standard 50mm, 75mm, 100mm)
            5. Select next standard tray size
            
            **Example:**
            - 5 × 50mm² cables (27mm diameter each)
            - Area per cable = π × (13.5)² = 573 mm²
            - Total area = 5 × 573 = 2865 mm²
            - For 50mm deep tray at 40% fill: 2865 / (50 × 0.4) = 143mm width
            - Select 150mm wide tray
            
            **Installation Rules:**
            - Maintain spacing between trays: 300mm minimum
            - Support spacing: 1.5m for horizontal, 2m for vertical
            - 25% spare capacity for future cables
            - Segregate power, control, and data cables
            - Use fire stopping at wall/floor penetrations
            """,
            
            "earth_system": """
            **📚 EARTHING SYSTEM FOR INSTALLERS (SS 638):**
            
            **Purpose of Earthing:**
            - Protect against electric shock
            - Provide path for fault current
            - Stabilize voltage during transients
            
            **Earth Pit Installation:**
            1. **Location:** Outside building, accessible for testing
            2. **Depth:** Minimum 3 meters
            3. **Electrode:** 20mm diameter copper-clad steel rod
            4. **Backfill:** Bentonite mix (improves conductivity)
            5. **Cover:** Heavy-duty cast iron with lock
            
            **Earth Resistance Targets:**
            - Combined system: < 1Ω
            - Generator neutral: < 1Ω
            - Lightning protection: < 10Ω
            - Fuel tank: < 10Ω
            
            **Test Link Installation:**
            - Install removable link at accessible location
            - Allows isolation for earth resistance testing
            - Must be clearly labeled
            - Rated for fault current
            
            **Bonding Requirements:**
            - Bond all metal enclosures, cable trays, pipework
            - Main equipotential bonding: 25mm² minimum
            - Supplementary bonding: 4mm² minimum
            - Bonding at building entry for all services
            """,
            
            "lightning_protection": """
            **📚 LIGHTNING PROTECTION FOR INSTALLERS (SS 555):**
            
            **Components:**
            1. **Air Terminals (Lightning Rods):** Capture lightning strikes
            2. **Down Conductors:** Carry current to earth
            3. **Earth Terminations:** Dissipate current safely
            4. **Test Joints:** Allow testing of continuity
            
            **Installation Rules:**
            
            **Air Terminals:**
            - Height: Minimum 0.5m above roof surface
            - Spacing: Based on protection level (typically 5-15m)
            - Material: Copper or aluminum (16mm diameter min)
            - Location: Along perimeter, ridges, high points
            
            **Down Conductors:**
            - Spacing: Maximum 20m along perimeter
            - Routing: Straightest path to earth
            - Protection: In PVC conduit up to 2m height
            - Bonding: Connect to main earth bar at base
            
            **Test Joints:**
            - One per down conductor
            - Located 1.5m above ground
            - Weatherproof enclosure
            - Bolted link type for disconnection
            
            **Common Mistakes:**
            - Sharp bends in conductors (avoid < 90°)
            - Poor bonding of metal objects
            - Insufficient separation from data cables
            - Missing test joints
            """,
            
            "generator_installation": """
            **📚 GENERATOR INSTALLATION FOR INSTALLERS:**
            
            **Location Requirements:**
            - Ventilation: Adequate air intake and exhaust
            - Access: Minimum 1m clearance around unit
            - Fuel: Day tank (8hr min), main tank location
            - Acoustic: Sound attenuation for neighbors
            
            **Electrical Connections:**
            1. **Cable Sizing:** Based on generator full load current
            2. **Voltage Drop:** Keep < 3% at full load
            3. **ATS Installation:** Automatic transfer switch
            4. **Earth Connection:** Separate earth pits
            
            **Commissioning Tests:**
            - No-load run (30 minutes)
            - Load bank test (25%, 50%, 75%, 100%)
            - Transfer test (mains to generator)
            - Protection tests (earth fault, overcurrent)
            
            **Safety Features:**
            - Emergency stop button (external)
            - Battery charger with float mode
            - Fuel leak detection
            - Fire suppression system
            - Exhaust extraction
            """,
            
            "switchroom": """
            **📚 SWITCHROOM INSTALLATION GUIDE:**
            
            **Clearance Requirements (SS 638):**
            - Front: 1500mm for ACB withdrawal
            - Rear: 800mm for termination access
            - Sides: 800mm for ventilation
            - Top: 500mm for busbar access
            
            **Ventilation:**
            - Temperature: Maintain below 35°C
            - Air changes: Minimum 6 per hour
            - Mechanical ventilation or AC
            - Positive pressure to prevent dust
            
            **Lighting:**
            - Minimum 300 lux at floor level
            - Emergency lighting on generator
            - Local switches at entrance
            
            **Safety Equipment:**
            - Rubber matting in front of switchboards
            - Fire extinguisher (CO2 type)
            - "DANGER - HIGH VOLTAGE" signs
            - Single line diagram on wall
            - Emergency lighting
            
            **Cable Entry:**
            - Gland plates at bottom/top
            - Fire stopping at penetrations
            - Cable supports within 1m of entry
            - Segregation of different voltages
            """
        }
        return notes.get(topic, "No notes available for this topic")
    
    # ==================== TECHNICAL CALCULATIONS ====================
    
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
    
    def calculate_cable_tray_size(self, cables, tray_depth=50, tray_type="perforated", spare_capacity=0.25):
        """
        Calculate required cable tray size based on cable diameters
        cables: list of cable sizes in sqmm
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
                    "area": area
                })
        
        # Apply spare capacity
        total_area_with_spare = total_area * (1 + spare_capacity)
        
        # Calculate required width based on fill factor
        fill_factor = self.tray_fill_factors.get(tray_type, 0.4)
        required_width = total_area_with_spare / (tray_depth * fill_factor)
        
        # Select standard tray size
        selected_width = next((w for w in self.standard_tray_sizes if w >= required_width), 
                              self.standard_tray_sizes[-1])
        
        # Calculate actual fill percentage
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
    
    def calculate_room_load(self, room_type, area_m2, quantity=1):
        """
        Calculate electrical load for a specific room type
        """
        if room_type not in self.room_load_database:
            return None
        
        room = self.room_load_database[room_type]
        
        # Calculate individual loads
        lighting_load = room["lighting_load"] * area_m2 / 1000  # kW
        socket_load = room["socket_load"] * area_m2 / 1000      # kW
        equipment_load = room["equipment_load"] * area_m2 / 1000 # kW
        ac_load = room["ac_load"] * area_m2 / 1000              # kW
        
        # Total before diversity
        total_raw = lighting_load + socket_load + equipment_load + ac_load
        
        # Apply diversity factor
        total_diversified = total_raw * room["diversity_factor"]
        
        # Calculate per quantity
        total_with_quantity = total_diversified * quantity
        
        # Calculate current
        current = (total_with_quantity * 1000) / (math.sqrt(3) * 400 * 0.85)
        
        return {
            "room_type": room_type,
            "description": room["description"],
            "area_m2": area_m2,
            "quantity": quantity,
            "lighting_load_kw": lighting_load,
            "socket_load_kw": socket_load,
            "equipment_load_kw": equipment_load,
            "ac_load_kw": ac_load,
            "total_raw_kw": total_raw,
            "diversity_factor": room["diversity_factor"],
            "total_diversified_kw": total_diversified,
            "total_with_quantity_kw": total_with_quantity,
            "current_a": current,
            "typical_equipment": room["typical_equipment"],
            "special_requirements": room.get("special_requirements", [])
        }
    
    def calculate_building_total_load(self, room_loads):
        """
        Calculate total building load from multiple rooms
        """
        total_lighting = sum(r["lighting_load_kw"] * r["quantity"] for r in room_loads)
        total_socket = sum(r["socket_load_kw"] * r["quantity"] for r in room_loads)
        total_equipment = sum(r["equipment_load_kw"] * r["quantity"] for r in room_loads)
        total_ac = sum(r["ac_load_kw"] * r["quantity"] for r in room_loads)
        total_diversified = sum(r["total_with_quantity_kw"] for r in room_loads)
        
        # Overall building diversity (typically 0.6-0.8)
        building_diversity = 0.7
        final_load = total_diversified * building_diversity
        
        return {
            "total_lighting_kw": total_lighting,
            "total_socket_kw": total_socket,
            "total_equipment_kw": total_equipment,
            "total_ac_kw": total_ac,
            "total_diversified_kw": total_diversified,
            "building_diversity": building_diversity,
            "final_load_kw": final_load,
            "final_current_a": (final_load * 1000) / (math.sqrt(3) * 400 * 0.85)
        }
    
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
    
    # ==================== CHECKLISTS ====================
    
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
st.set_page_config(page_title="SG Electrical Design Pro - Complete Guide for Installers", layout="wide")
engine = SGProEngine()

st.title("⚡ Singapore Electrical Design Professional")
st.subheader("Complete Design Guide for Installers & Junior Engineers")
st.markdown("**Compliant with SS 638, SS 555, SP Group & BCA Requirements**")

# Sidebar with quick reference
with st.sidebar:
    st.header("📋 Quick Reference")
    st.info("**SS 638:** Singapore Standard for Electrical Installations")
    st.info("**SS 555:** Lightning Protection Standard")
    st.info("**SP Group:** Utility Technical Requirements")
    
    st.divider()
    
    st.header("📐 Design Input Parameters")
    
    with st.expander("⚡ Main Electrical Parameters", expanded=True):
        load_kw = st.number_input("Design Load (kW)", value=100.0)
        pf = st.slider("Power Factor", 0.7, 1.0, 0.85)
        voltage = 400  # Standard 3-Phase SG
        ib = (load_kw * 1000) / (math.sqrt(3) * voltage * pf)
        
        cable_length = st.number_input("Cable Length from Source (m)", min_value=1.0, value=50.0)
        max_vd_percent = st.slider("Max Voltage Drop (%)", 1.0, 8.0, 4.0, 0.5)
    
    with st.expander("🏢 Building Information"):
        building_length = st.number_input("Building Length (m)", min_value=1.0, value=50.0)
        building_width = st.number_input("Building Width (m)", min_value=1.0, value=30.0)
        building_height = st.number_input("Building Height (m)", min_value=1.0, value=15.0)
        roof_type = st.selectbox("Roof Type", ["Flat", "Pitched"])
        protection_level = st.selectbox("Lightning Protection Level", 
                                       ["Level I", "Level II", "Level III", "Level IV"], 
                                       index=2)
    
    with st.expander("🔧 Installation Details"):
        num_sub_feeders = st.number_input("Number of Outgoing Feeders", min_value=1, value=5)
        include_spare = st.checkbox("Include 20% Future Spare Space", value=True)

# Create main tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
    "📚 INSTALLER'S GUIDE",  # Educational section for installers
    "📊 Main MSB Design", 
    "🏢 Room Load Calculator",
    "🔌 Cable & Containment",
    "🔄 Generator Systems", 
    "⛓️ Earthing Design", 
    "⚡ Lightning Protection", 
    "💡 Emergency Lighting",
    "📋 Project Checklists",
    "🛠️ Maintenance & Troubleshooting"
])

# ==================== TAB 1: INSTALLER'S GUIDE (EDUCATIONAL) ====================
with tab1:
    st.header("📚 ELECTRICAL INSTALLATION GUIDE FOR INSTALLERS & JUNIOR ENGINEERS")
    st.write("**Singapore Standards (SS 638, SS 555) Compliant**")
    st.write("---")
    
    st.info("""
    **👷 HOW TO USE THIS APPLICATION:**
    This tool is designed to guide you through the complete electrical design process.
    Each tab provides calculations AND explanations of WHY and HOW to do it correctly.
    
    **For Junior Engineers:** Read the educational notes in each section to understand the theory.
    **For Installers:** Follow the step-by-step guides and checklists for proper installation.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎓 BASIC ELECTRICAL THEORY")
        
        with st.expander("📐 Ohm's Law & Power Calculations"):
            st.markdown("""
            **Ohm's Law:** V = I × R
            - V = Voltage (Volts)
            - I = Current (Amperes)
            - R = Resistance (Ohms)
            
            **Power in 3-Phase Systems:**
            - P (kW) = √3 × V × I × PF ÷ 1000
            - I (Amps) = P × 1000 ÷ (√3 × V × PF)
            
            **Example:** 
            100kW load at 400V, 0.85PF
            I = 100,000 ÷ (1.732 × 400 × 0.85) = 170 Amps
            """)
        
        with st.expander("🔋 Power Factor Explained"):
            st.markdown("""
            **Power Factor (PF)** = Real Power (kW) ÷ Apparent Power (kVA)
            
            - **PF = 1.0:** Pure resistive load (heaters, lights)
            - **PF = 0.8-0.9:** Typical motors, transformers
            - **PF < 0.8:** Poor power factor (waste energy)
            
            **Why it matters:**
            - Lower PF = Higher current = Larger cables
            - SP Group charges penalty for PF < 0.85
            - Fix with capacitor banks
            """)
        
        with st.expander("🔌 Cable Current Rating (Iz)"):
            st.markdown("""
            **Iz** = Current carrying capacity of cable
            
            **Factors affecting Iz:**
            1. Installation method (air, conduit, buried)
            2. Ambient temperature
            3. Grouping of cables
            4. Insulation type (XLPE, PVC)
            
            **Rule of thumb:** Select cable with Iz ≥ 1.25 × Ib
            - Ib = Design current
            - 25% safety margin for continuous load
            """)
        
        with st.expander("📉 Voltage Drop Explained"):
            st.markdown("""
            **Voltage Drop** = Loss of voltage along cable length
            
            **SS 638 Limits:**
            - Lighting circuits: 3% maximum
            - Power circuits: 5% maximum
            - Overall installation: 4% typical
            
            **Formula:** Vd = √3 × I × L × (R cosφ + X sinφ) ÷ 1000
            
            **Consequences of high Vd:**
            - Motors run hot, lose torque
            - Lights dim
            - Equipment malfunctions
            - Energy waste
            """)
    
    with col2:
        st.subheader("📋 SS 638 QUICK REFERENCE")
        
        with st.expander("🔧 Installation Methods (Reference)"):
            st.markdown("""
            **Method A:** Conduit in insulated wall
            **Method B:** Conduit on wall surface
            **Method C:** Direct in plaster
            **Method E:** In free air (cable tray)
            **Method D:** Buried direct in ground
            
            **Most common:** Method E for cable tray installations
            """)
        
        with st.expander("🌡️ Derating Factors"):
            st.markdown("""
            **Ambient Temperature (Method E):**
            - 30°C: 1.00
            - 35°C: 0.96
            - 40°C: 0.91
            - 45°C: 0.87
            
            **Grouping (touching):**
            - 2 cables: 0.80
            - 3 cables: 0.70
            - 4 cables: 0.65
            - 5 cables: 0.60
            
            **Always apply derating to Iz!**
            """)
        
        with st.expander("🛡️ Protection Types"):
            st.markdown("""
            **MCB** (Miniature Circuit Breaker):
            - Up to 63A
            - For lighting, socket outlets
            
            **MCCB** (Moulded Case CB):
            - 100A to 1600A
            - For sub-mains, large loads
            
            **ACB** (Air Circuit Breaker):
            - 800A and above
            - For main incomer, generators
            
            **RCCB/ELCB** (Earth Leakage):
            - 30mA for shock protection
            - 100-300mA for fire protection
            """)
        
        with st.expander("⚡ Earthing Types (TT, TN-S, TN-C-S)"):
            st.markdown("""
            **Singapore uses TT System:**
            - Each building has own earth electrodes
            - Independent of utility earth
            
            **TN-S:** Separate neutral and earth throughout
            **TN-C-S:** Combined neutral/earth (PEN) in supply
            
            **Key requirement:** Earth resistance < 1Ω combined
            """)
    
    st.divider()
    
    # Step-by-step design process
    st.subheader("👷 STEP-BY-STEP DESIGN PROCESS")
    
    steps = [
        ("1. Load Assessment", "Calculate all loads, apply diversity", "Complete"),
        ("2. Cable Sizing", "Size based on current + voltage drop", "Complete"),
        ("3. Protection Selection", "Select breakers, coordinate protection", "Complete"),
        ("4. Cable Containment", "Size cable trays, trunking", "Complete"),
        ("5. Generator Sizing", "Essential loads + starting currents", "Complete"),
        ("6. Earthing Design", "Earth pits, bonding, test links", "Complete"),
        ("7. Lightning Protection", "Air terminals, down conductors", "Complete"),
        ("8. Emergency Lighting", "Escape route coverage", "Complete"),
        ("9. Switchboard Layout", "Physical arrangement, clearances", "Complete"),
        ("10. Documentation", "Single line diagrams, schedules", "Complete")
    ]
    
    for step, desc, status in steps:
        st.markdown(f"**{step}** - {desc}  ✅")

# ==================== TAB 2: MAIN MSB DESIGN ====================
with tab2:
    st.header("📊 Main Switchboard (MSB) Design")
    st.write("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.info("### 📋 Breaker & Cable Schedule")
        
        # Calculate main breaker
        at, af = engine.get_at_af(ib)
        b_type = "ACB" if af >= 800 else "MCCB" if af > 63 else "MCB"
        
        st.metric("Design Current (Ib)", f"{ib:.2f} A")
        st.success(f"**Incomer:** {at}AT / {af}AF {b_type}")
        
        # Cable selection with voltage drop
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
        
        st.divider()
        
        # Educational note
        with st.expander("📚 HOW TO SELECT MAIN BREAKER (For Junior Engineers)"):
            st.markdown(engine.get_installer_notes("cable_sizing"))
    
    with col2:
        st.warning("### 📏 Switchroom Layout Requirements")
        
        # Calculate MSB physical size
        base_width = 800 if b_type == "ACB" else 600
        sub_feeder_width = (num_sub_feeders * 400)
        metering_width = 400 if at > 100 else 0
        total_width = base_width + sub_feeder_width + metering_width
        
        if include_spare:
            total_width *= 1.2
        
        # Clearance data
        clearance_data = {
            "Position": ["Front (Withdrawal)", "Rear (Terminations)", "Left Side", "Right Side", "Top"],
            "Minimum": ["1500 mm", "800 mm", "800 mm", "800 mm", "500 mm"],
            "Purpose": ["ACB removal", "Cable termination", "Access/Ventilation", "Access/Ventilation", "Busbar access"]
        }
        st.table(clearance_data)
        
        st.write(f"**Estimated MSB Width:** {total_width:.0f} mm")
        st.info(f"**Room Depth Required:** Front(1500) + Board(800) + Rear(800) = 3100 mm")
        
        # Educational note
        with st.expander("📚 SWITCHROOM INSTALLATION GUIDE"):
            st.markdown(engine.get_installer_notes("switchroom"))

# ==================== TAB 3: ROOM LOAD CALCULATOR ====================
with tab3:
    st.header("🏢 Room Electrical Load Calculator")
    st.write("Calculate power requirements for different room types based on SS 638 guidelines")
    st.write("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("➕ Add Rooms")
        
        # Room selection interface
        room_types = list(engine.room_load_database.keys())
        selected_rooms = []
        
        num_room_types = st.number_input("Number of different room types", min_value=1, max_value=10, value=3)
        
        for i in range(num_room_types):
            st.markdown(f"**Room Type {i+1}**")
            col_room, col_area, col_qty = st.columns(3)
            with col_room:
                room_type = st.selectbox(f"Type", room_types, key=f"room_type_{i}")
            with col_area:
                area = st.number_input(f"Area (m²)", min_value=1.0, value=100.0, key=f"room_area_{i}")
            with col_qty:
                qty = st.number_input(f"Quantity", min_value=1, value=1, key=f"room_qty_{i}")
            
            selected_rooms.append({
                "type": room_type,
                "area": area,
                "quantity": qty
            })
            st.divider()
    
    with col2:
        st.subheader("📊 Calculated Loads")
        
        if selected_rooms:
            room_loads = []
            total_load = 0
            
            for room in selected_rooms:
                result = engine.calculate_room_load(room["type"], room["area"], room["quantity"])
                if result:
                    room_loads.append(result)
                    
                    with st.expander(f"**{room['type']}** (Qty: {room['quantity']} × {room['area']}m²)"):
                        st.write(f"Description: {result['description']}")
                        st.write(f"Lighting: {result['lighting_load_kw']:.2f} kW")
                        st.write(f"Sockets: {result['socket_load_kw']:.2f} kW")
                        st.write(f"Equipment: {result['equipment_load_kw']:.2f} kW")
                        st.write(f"Air Conditioning: {result['ac_load_kw']:.2f} kW")
                        st.write(f"**Total (after diversity): {result['total_with_quantity_kw']:.2f} kW**")
                        st.write(f"**Current: {result['current_a']:.1f} A**")
                        
                        st.write("**Typical Equipment:**")
                        for eq in result['typical_equipment'][:3]:
                            st.write(f"- {eq}")
                        
                        if result['special_requirements']:
                            st.write("**Special Requirements:**")
                            for req in result['special_requirements']:
                                st.write(f"- {req}")
            
            # Calculate building total
            if room_loads:
                total = engine.calculate_building_total_load(room_loads)
                
                st.success("### 🏢 BUILDING TOTAL")
                st.write(f"**Total Diversified Load:** {total['final_load_kw']:.2f} kW")
                st.write(f"**Total Current:** {total['final_current_a']:.1f} A")
                
                # Recommend main breaker
                at_total, af_total = engine.get_at_af(total['final_current_a'])
                st.info(f"**Recommended Main Breaker:** {at_total}AT / {af_total}AF")
    
    # Educational note
    with st.expander("📚 ROOM LOAD CALCULATION GUIDE (SS 638)"):
        st.markdown("""
        **Room Load Calculation Principles:**
        
        1. **Lighting Load:** Based on W/m² from SS 638
           - Office: 15 W/m²
           - Carpark: 5 W/m²
           - Staircase: 8 W/m²
        
        2. **Socket Outlet Load:** 
           - General offices: 25 W/m²
           - Assume 50% diversity
        
        3. **Equipment Load:**
           - Computers, printers, etc.
           - Special equipment (servers, medical) calculated separately
        
        4. **Diversity Factors:**
           - Not all equipment runs simultaneously
           - Apply diversity per SS 638 Table 1A
           - Overall building diversity: 0.6-0.8
        
        5. **Future Expansion:**
           - Always include 20-30% spare capacity
           - Allow for future tenancy changes
        """)

# ==================== TAB 4: CABLE & CONTAINMENT ====================
with tab4:
    st.header("🔌 Cable & Containment Sizing")
    st.write("Calculate cable tray/trunking sizes based on cable quantities")
    st.write("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Cable Tray Sizing")
        
        # Input cables for tray
        st.write("**Select cables to install in tray:**")
        
        available_cables = list(engine.cable_db.keys())
        num_cables = st.number_input("Number of different cable sizes", min_value=1, value=3, key="num_tray_cables")
        
        cables_in_tray = []
        for i in range(num_cables):
            col_size, col_qty = st.columns(2)
            with col_size:
                cable_size = st.selectbox(f"Cable {i+1} size", available_cables, key=f"tray_cable_{i}")
            with col_qty:
                qty = st.number_input(f"Quantity", min_value=1, value=3, key=f"tray_qty_{i}")
            
            for _ in range(qty):
                cables_in_tray.append(cable_size)
        
        # Tray parameters
        tray_depth = st.selectbox("Tray depth (mm)", [50, 75, 100, 150])
        tray_type = st.selectbox("Tray type", ["perforated", "ladder", "solid", "wire_mesh"])
        spare_capacity = st.slider("Spare capacity %", 0, 50, 25) / 100
        
        if st.button("Calculate Tray Size", type="primary"):
            result = engine.calculate_cable_tray_size(cables_in_tray, tray_depth, tray_type, spare_capacity)
            
            with col2:
                st.subheader("📊 Tray Sizing Results")
                
                st.write(f"**Total Cable Area:** {result['total_cable_area']:.0f} mm²")
                st.write(f"**With {spare_capacity*100:.0f}% Spare:** {result['total_area_with_spare']:.0f} mm²")
                st.write(f"**Required Width:** {result['required_width']:.0f} mm")
                st.write(f"**Selected Tray Width:** {result['selected_width']} mm")
                st.write(f"**Actual Fill:** {result['actual_fill_percentage']:.1f}%")
                
                if result['actual_fill_percentage'] <= result['fill_factor'] * 100:
                    st.success("✅ Tray size is adequate")
                else:
                    st.error("⚠️ Tray is overfilled - select larger size")
                
                st.write("**Cable Details:**")
                for cable in result['cable_details']:
                    st.write(f"- {cable['size']}mm²: Ø{cable['diameter']}mm, Area {cable['area']:.0f}mm²")
    
    # Educational notes
    st.divider()
    with st.expander("📚 CABLE CONTAINMENT INSTALLATION GUIDE", expanded=True):
        st.markdown(engine.get_installer_notes("cable_containment"))
    
    with st.expander("📚 CABLE SIZING STEP-BY-STEP"):
        st.markdown(engine.get_installer_notes("cable_sizing"))

# ==================== TAB 5: GENERATOR SYSTEMS ====================
with tab5:
    st.header("🔄 Generator Sizing for Essential & Fire Services")
    st.write("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Essential Loads (Must Run During Power Outage)")
        
        # Lift inputs
        st.write("**🚡 Lift Motors (Homing Function)**")
        num_lifts = st.number_input("Number of Lifts", min_value=0, value=2, key="gen_num_lifts")
        lift_loads = []
        lift_starting_kvas = []
        
        for i in range(num_lifts):
            lift_kw = st.number_input(f"Lift {i+1} Motor (kW)", value=10.0, key=f"gen_lift_{i}_kw")
            lift_pf = st.slider(f"Lift {i+1} PF", 0.7, 1.0, 0.85, key=f"gen_lift_{i}_pf")
            lift_type = st.selectbox(f"Lift {i+1} Starting Type", 
                                    ["Lift (Variable Speed)", "Lift (Star-Delta)"], 
                                    key=f"gen_lift_{i}_type")
            
            running_kva = (lift_kw * 1000) / (math.sqrt(3) * voltage * lift_pf) / 1000
            starting_multiplier = engine.motor_starting_multipliers[lift_type]
            starting_kva = running_kva * starting_multiplier
            
            lift_loads.append(running_kva)
            lift_starting_kvas.append(starting_kva)
            
            st.caption(f"  Running: {running_kva:.1f} kVA | Starting: {starting_kva:.1f} kVA")
        
        # Other essential loads
        st.write("**🏢 Other Essential Loads**")
        num_essential = st.number_input("Number of Other Essential Loads", min_value=0, value=2, key="gen_num_essential")
        essential_loads = lift_loads.copy()
        
        for i in range(num_essential):
            load_desc = st.text_input(f"Load {i+1} Description", value=f"Essential Load {i+1}", key=f"gen_ess_desc_{i}")
            load_kva = st.number_input(f"{load_desc} (kVA)", value=5.0, key=f"gen_ess_load_{i}")
            essential_loads.append(load_kva)
    
    with col2:
        st.subheader("🔥 Fire Fighting Loads (Must Run During Fire)")
        
        # Fire pump inputs
        st.write("**🚒 Fire Pump System**")
        has_fire_pump = st.checkbox("Include Fire Pump", value=True, key="gen_has_fire_pump")
        
        fire_loads = []
        fire_starting_kvas = []
        
        if has_fire_pump:
            main_pump_kw = st.number_input("Main Fire Pump Motor (kW)", value=30.0, key="gen_main_pump_kw")
            main_pump_pf = st.slider("Main Fire Pump PF", 0.7, 1.0, 0.85, key="gen_main_pump_pf")
            pump_type = st.selectbox("Fire Pump Starting Type", 
                                    ["Fire Pump (Direct Online)", "Fire Pump (Star-Delta)", "Fire Pump (Soft Starter)"],
                                    key="gen_pump_type")
            
            running_kva = (main_pump_kw * 1000) / (math.sqrt(3) * voltage * main_pump_pf) / 1000
            starting_multiplier = engine.motor_starting_multipliers[pump_type]
            starting_kva = running_kva * starting_multiplier
            
            fire_loads.append(running_kva)
            fire_starting_kvas.append(starting_kva)
            
            st.caption(f"  Running: {running_kva:.1f} kVA | Starting: {starting_kva:.1f} kVA")
            
            # Jockey pump
            has_jockey = st.checkbox("Include Jockey Pump", value=True, key="gen_has_jockey")
            if has_jockey:
                jockey_kw = st.number_input("Jockey Pump Motor (kW)", value=2.2, key="gen_jockey_kw")
                jockey_pf = st.slider("Jockey Pump PF", 0.7, 1.0, 0.85, key="gen_jockey_pf")
                jockey_running = (jockey_kw * 1000) / (math.sqrt(3) * voltage * jockey_pf) / 1000
                fire_loads.append(jockey_running)
                st.caption(f"  Jockey Pump Running: {jockey_running:.1f} kVA")
        
        # Pressurization fans
        st.write("**💨 Staircase Pressurization Fans**")
        num_fans = st.number_input("Number of Pressurization Fans", min_value=0, value=2, key="gen_num_fans")
        
        for i in range(num_fans):
            fan_kw = st.number_input(f"Fan {i+1} Motor (kW)", value=5.5, key=f"gen_fan_{i}_kw")
            fan_pf = st.slider(f"Fan {i+1} PF", 0.7, 1.0, 0.85, key=f"gen_fan_{i}_pf")
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
    
    st.success(f"✅ **Final Recommendation:** Select a **{recommended_gen:.0f} kVA** generator (Prime Rating)")
    
    # Educational note
    with st.expander("📚 GENERATOR INSTALLATION GUIDE"):
        st.markdown(engine.get_installer_notes("generator_installation"))

# ==================== TAB 6: EARTHING DESIGN ====================
with tab6:
    st.header("⛓️ Earthing System Design")
    st.write("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Earth Pit Configuration")
        
        has_fuel_tank = st.checkbox("Separate Fuel Tank Present", value=True, key="earth_has_fuel")
        soil_condition = st.selectbox("Soil Condition", ["Normal", "Poor (High Resistance)"], key="earth_soil")
        building_area = building_length * building_width
        
        st.info(f"**Building Area:** {building_area:.0f} m²")
        
        earth_pits = engine.calculate_earth_pits(has_fuel_tank, soil_condition, building_area, protection_level)
        
        st.write("**Recommended Earth Pits:**")
        st.write(f"- Generator Body/Neutral: **{earth_pits['generator_body']} pits**")
        if earth_pits['fuel_tank'] > 0:
            st.write(f"- Fuel Tank: **{earth_pits['fuel_tank']} pit**")
        st.write(f"- Lightning Protection: **{earth_pits['lightning_protection']} pits**")
        st.write(f"**Total Earth Pits Required: {earth_pits['total_recommended']}**")
        
        # Earth pit specification
        st.subheader("🔧 Earth Pit Specification")
        st.markdown("""
        **Standard Earth Pit Requirements:**
        - Depth: Minimum 3 meters
        - Electrode: Copper-clad steel rod (20mm diameter)
        - Backfill: Bentonite mix
        - Cover: Heavy-duty cast iron with lock
        - Test link: Removable link
        """)
    
    with col2:
        st.subheader("Test Link Point Requirements")
        
        st.markdown("""
        **Test Link Configuration:**
        - Install **bolted removable link** in main earthing conductor
        - Location: Between generator neutral and main earth
        - Purpose: Allows isolation for earth resistance testing
        - Rating: Copper link rated for fault current
        """)
        
        st.warning("**⚠️ Important Safety Notes:**")
        st.markdown("""
        - Test link must be accessible only to authorized personnel
        - Clear labeling required
        - Include in maintenance schedule
        """)
        
        # Earth resistance requirements
        st.subheader("📊 Earth Resistance Targets")
        resistance_data = {
            "System": ["Generator Neutral", "Lightning Protection", "Fuel Tank", "Combined System"],
            "Max Ω": ["1 Ω", "10 Ω", "10 Ω", "1 Ω"]
        }
        st.table(resistance_data)
    
    # Educational note
    with st.expander("📚 EARTHING INSTALLATION GUIDE"):
        st.markdown(engine.get_installer_notes("earth_system"))

# ==================== TAB 7: LIGHTNING PROTECTION ====================
with tab7:
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
        st.write(f"- Dimensions: {building_length}m L × {building_width}m W × {building_height}m H")
        st.write(f"- Area: {lp_results['building_area']:.0f} m²")
        st.write(f"- Perimeter: {lp_results['perimeter']:.0f} m")
        st.write(f"- Protection Level: {protection_level}")
        
        st.subheader("🎯 Protection Parameters")
        st.write(f"- Protection Angle: {lp_results['protection_angle']}°")
        st.write(f"- Mesh Size: {lp_results['mesh_size']}m")
        st.write(f"- Rolling Sphere Radius: {lp_results['rolling_sphere_radius']}m")
        st.write(f"- Terminal Spacing: {lp_results['terminal_spacing']}m")
    
    with col2:
        st.subheader("📋 Bill of Materials")
        
        lp_data = {
            "Component": [
                "Air Terminals",
                "Down Conductors",
                "Test Joints",
                "Roof Conductor",
                "Down Conductor Length",
                "Total Conductor"
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
    
    # Installation guidelines
    st.subheader("📍 Installation Guidelines")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.write("**Air Terminals:**")
        st.markdown(f"""
        - Quantity: **{lp_results['num_air_terminals']}** terminals
        - Spacing: **{lp_results['terminal_spacing']}m** between terminals
        - Height: Minimum 0.5m above roof
        - Material: Copper or aluminum (16mm ø min)
        """)
    
    with col4:
        st.write("**Down Conductors:**")
        st.markdown(f"""
        - Quantity: **{lp_results['num_down_conductors']}** conductors
        - Spacing: Maximum 20m along perimeter
        - Routing: Straightest path to earth
        - Protection: In PVC conduit up to 2m height
        """)
    
    # Educational note
    with st.expander("📚 LIGHTNING PROTECTION INSTALLATION GUIDE"):
        st.markdown(engine.get_installer_notes("lightning_protection"))

# ==================== TAB 8: EMERGENCY LIGHTING ====================
with tab8:
    st.header("💡 Emergency Lighting Design")
    st.write("Compliant with SS 563 & Fire Code")
    st.write("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Lighting Inventory")
        
        total_lights = st.number_input("Total Number of Light Fittings", min_value=1, value=200, key="emergency_total_lights")
        
        st.write("**Connection Strategy:**")
        escape_percent = st.slider("Escape Route Lights (% to connect)", 0, 100, 100, key="emergency_escape_percent")
        general_percent = st.slider("General Area Lights (% to connect)", 0, 100, 30, key="emergency_general_percent")
        
        emergency_calc = engine.calculate_emergency_lights(total_lights, escape_percent, general_percent)
        
        st.write("**Results:**")
        st.write(f"- Escape Route Lights: **{emergency_calc['escape_route_lights']}**")
        st.write(f"- General Area Lights: **{emergency_calc['general_area_lights']}**")
        st.write(f"- Exit Signs: **{emergency_calc['exit_signs']}**")
        st.write(f"- **Total Emergency Lights: {emergency_calc['total_emergency_lights']}**")
        
        st.metric("Emergency Lighting Load", f"{emergency_calc['emergency_load_watts']/1000:.2f} kW")
    
    with col2:
        st.subheader("Connection Requirements")
        
        st.markdown("""
        **Connection Methods:**
        
        1. **Dedicated Emergency Busbar**
           - All emergency lights on dedicated section
           - Auto-transfer to generator
        
        2. **Contactor Control**
           - Selected circuits switched to generator
           - More economical for large installations
        
        **Design Checklist:**
        """)
        
        st.checkbox("Emergency lights on separate circuits", value=True, disabled=True, key="emergency_check1")
        st.checkbox("Exit signs maintained (always on)", value=True, disabled=True, key="emergency_check2")
        st.checkbox("Minimum 1 lux on escape routes", value=True, disabled=True, key="emergency_check3")
        st.checkbox("Test facilities provided", value=True, disabled=True, key="emergency_check4")
        st.checkbox("Green dot marking on fittings", value=True, disabled=True, key="emergency_check5")
        
        st.info("ℹ️ Comply with SS 563 & Fire Code requirements")

# ==================== TAB 9: PROJECT CHECKLISTS ====================
with tab9:
    st.header("📋 Complete Project Checklists")
    st.write("Use these checklists to ensure nothing is missed")
    st.write("---")
    
    design_checklist = engine.generate_design_checklist()
    install_checklist = engine.generate_installation_checklist()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📐 DESIGN STAGE CHECKLIST")
        for category, items in design_checklist.items():
            with st.expander(f"### {category}"):
                for item in items:
                    st.checkbox(item, key=f"design_{category}_{item}")
    
    with col2:
        st.subheader("🔧 INSTALLATION STAGE CHECKLIST")
        for category, items in install_checklist.items():
            with st.expander(f"### {category}"):
                for item in items:
                    st.checkbox(item, key=f"install_{category}_{item}")
    
    # Documentation requirements
    st.divider()
    st.subheader("📸 Required Documentation")
    
    doc_col1, doc_col2, doc_col3 = st.columns(3)
    
    with doc_col1:
        st.markdown("""
        **Design Documents:**
        - Single line diagrams
        - Load schedules
        - Cable schedules
        - Equipment specifications
        - Protection studies
        - Voltage drop calcs
        """)
    
    with doc_col2:
        st.markdown("""
        **Installation Records:**
        - Method statements
        - Risk assessments
        - Material certificates
        - Site photos
        - Inspection reports
        - Test reports
        """)
    
    with doc_col3:
        st.markdown("""
        **As-Built Documents:**
        - Updated single line diagrams
        - Equipment manuals
        - Warranty certificates
        - Commissioning reports
        - Maintenance schedules
        """)

# ==================== TAB 10: MAINTENANCE & TROUBLESHOOTING ====================
with tab10:
    st.header("🛠️ Maintenance & Troubleshooting")
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
        st.text_area("Record maintenance activities:", height=100, key="maint_log")
        st.date_input("Next scheduled maintenance", key="maint_date")
    
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

# ==================== FOOTER ====================
st.divider()
st.markdown("""
**⚠️ IMPORTANT NOTES FOR INSTALLERS:**

1. **Always verify site conditions** before installation
2. **Follow SS 638** for all electrical installations
3. **Use calibrated test equipment** for all measurements
4. **Document everything** - photos, test results, as-built drawings
5. **Safety first** - use proper PPE, follow LOTO procedures
6. **Engage professional engineers** for final design approval
7. **Submit for inspections** before covering/cabling

**For Junior Engineers:** Study the educational notes in each section. Understanding the WHY is as important as the HOW.

**For Installers:** Use the checklists and follow the step-by-step guides. Quality installation prevents future problems.
""")

st.caption("© Singapore Electrical Design Professional - Version 2.0 | Compliant with SS 638:2024, SS 555, SP Group Requirements")
