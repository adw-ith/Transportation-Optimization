from train import Route, Package, Vehicle


# --- Define a Custom Logistics Network ---

# A set of named locations for our test scenario


LOCATIONS =['mumbai', 'chennai', 'delhi']
"""[
   "Central Depot",
    "North Hub",
    "South Retail",
    "East Industrial Park",
    "West Residential"
]"""

# The routes connecting the locations with specific distances
ROUTES = [Route(start_location='mumbai', end_location='chennai', distance=1233.45), Route(start_location='mumbai', end_location='delhi', distance=1403.45), Route(start_location='chennai', end_location='mumbai', distance=1230.31), Route(start_location='chennai', end_location='delhi', distance=2196.57), Route(start_location='delhi', end_location='mumbai', distance=1395.75), Route(start_location='delhi', end_location='chennai', distance=2185.43)]
"""  [Route("Central Depot", "North Hub", 12),
    Route("Central Depot", "East Industrial Park", 20),
    Route("North Hub", "West Residential", 15),
    Route("East Industrial Park", "South Retail", 10),
    Route("West Residential", "South Retail", 25)
]"""

# --- Define the Initial State for the Test ---

# A specific list of packages to be delivered
CUSTOM_PACKAGES =  [Package(id=0, pickup_location='mumbai', delivery_location='chennai', weight=1, status=0), Package(id=1, pickup_location='mumbai', delivery_location='delhi', weight=1, status=0)] 
"""    [Package(id=0, pickup_location="North Hub", delivery_location="South Retail", weight=8),
    Package(id=1, pickup_location="East Industrial Park", delivery_location="West Residential", weight=15),
    Package(id=2, pickup_location="Central Depot", delivery_location="West Residential", weight=5),
    Package(id=3, pickup_location="South Retail", delivery_location="North Hub", weight=12),
]"""

# A specific fleet of vehicles with their starting locations and capacities
CUSTOM_VEHICLES = [Vehicle(id=0, capacity=1000, current_location='mumbai', speed=1.0, cost_per_km=1.0, available_at_time=0)]
"""[
    Vehicle(id=0, capacity=20, current_location="Central Depot", speed=1.0, cost_per_km=1.0),
    Vehicle(id=1, capacity=30, current_location="North Hub", speed=1.0, cost_per_km=1.0),
]"""



{
  "locations": [
    "Warehouse",
    "Distribution Hub",
    "Customer_A",
    "Customer_B",
    "Customer_C"
  ],
  "routes": [
    { "start": "Warehouse", "end": "Distribution Hub", "distance": 50 },
    { "start": "Distribution Hub", "end": "Customer_A", "distance": 20 },
    { "start": "Distribution Hub", "end": "Customer_B", "distance": 25 },
    { "start": "Customer_A", "end": "Customer_C", "distance": 15 },
    { "start": "Customer_B", "end": "Customer_C", "distance": 10 }
  ],
  "packages": [
    {
      "id": 101,
      "pickup": "Warehouse",
      "delivery": "Customer_A",
      "weight": 15,
      "priority": 3
    },
    {
      "id": 102,
      "pickup": "Warehouse",
      "delivery": "Customer_B",
      "weight": 10,
      "priority": 1
    },
    {
      "id": 103,
      "pickup": "Warehouse",
      "delivery": "Customer_C",
      "weight": 25,
      "priority": 1
    },
    {
      "id": 104,
      "pickup": "Customer_A",
      "delivery": "Distribution Hub",
      "weight": 5,
      "priority": 2
    }
  ],
  "vehicles": [
    {
      "id": 1,
      "capacity": 50,
      "location": "Warehouse",
      "speed": 1.0,
      "cost_per_km": 1.5
    },
    {
      "id": 2,
      "capacity": 30,
      "location": "Distribution Hub",
      "speed": 1.5,
      "cost_per_km": 2.0
    }
  ]
}