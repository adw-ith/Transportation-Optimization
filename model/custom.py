from train import Route, Package, Vehicle


locations = ['mumbai', 'chennai', 'delhi'] 
routes = [Route(start_location='mumbai', end_location='chennai', distance=1233.45), Route(start_location='mumbai', end_location='delhi', distance=1403.45), Route(start_location='chennai', end_location='mumbai', distance=1230.31), Route(start_location='chennai', end_location='delhi', distance=2196.57), Route(start_location='delhi', end_location='mumbai', distance=1395.75), Route(start_location='delhi', end_location='chennai', distance=2185.43)] 
packages = [Package(id=0, pickup_location='mumbai', delivery_location='chennai', weight=3, status=0), Package(id=1, pickup_location='mumbai', delivery_location='delhi', weight=2, status=0)] 
vehicles = [Vehicle(id=0, capacity=1000, current_location='mumbai', speed=1.0, cost_per_km=1.0, available_at_time=0)]
