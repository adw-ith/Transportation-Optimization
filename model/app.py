# model/app.py
from flask import Flask, request, jsonify
from test import run_with_json
from train import Package, Vehicle, Route  # use your classes

app = Flask(__name__)

# Global variables so test.py can import them if needed
LOCATIONS = []
ROUTES = []
CUSTOM_PACKAGES = []
CUSTOM_VEHICLES = []


@app.route("/solve", methods=["POST"])
def solve():
    global LOCATIONS, ROUTES, CUSTOM_PACKAGES, CUSTOM_VEHICLES
    try:
        data = request.get_json(force=True)

        # Extract arrays from POST payload (match your format)
        LOCATIONS = data.get("LOCATIONS", [])

        ROUTES = [
            Route(r["start"], r["end"], r["distance"])
            for r in data.get("ROUTES", [])
        ]

        CUSTOM_PACKAGES = [
            Package(
                id=p["id"],
                pickup_location=p["pickup_location"],      # <-- from "pickup"
                delivery_location=p["delivery_location"],  # <-- from "delivery"
                weight=p["weight"],
                status=0  # or map priority if you want: status=p.get("priority", 0)
            )
            for p in data.get("CUSTOM_PACKAGES", [])
        ]

        CUSTOM_VEHICLES = [
            Vehicle(
                id=v["id"],
                capacity=v["capacity"],
                current_location=v["current_location"],  # <-- from "location"
                speed=v.get("speed", 1.0),
                cost_per_km=v.get("cost_per_km", 1.0),
                available_at_time=0,
            )
            for v in data.get("CUSTOM_VEHICLES", [])
        ]
        print("Received data:", data)
        print("Parsed LOCATIONS:", LOCATIONS)
        print("Parsed ROUTES:", ROUTES)
        # Build scenario JSON for simulation
        scenario_json = {
            "locations": LOCATIONS,
            "routes": [
                {"start": r.start_location, "end": r.end_location, "distance": r.distance}
                for r in ROUTES
            ],
            "packages": [
                {
                    "id": p.id,
                    "pickup": p.pickup_location,
                    "delivery": p.delivery_location,
                    "weight": p.weight,
                    "priority": getattr(p, "priority", 0)
                }
                for p in CUSTOM_PACKAGES
            ],
            "vehicles": [
                {
                    "id": 1,
                    "capacity": v.capacity,
                    "location": "Kottayam",
                    "speed": v.speed,
                    "cost_per_km": v.cost_per_km
                }
                for v in CUSTOM_VEHICLES
            ]
        }

        # Log for debugging
        with open("model_log.txt", "a") as f:
            print("LOCATIONS =", LOCATIONS, file=f)
            print("ROUTES =", ROUTES, file=f)
            print("CUSTOM_PACKAGES =", CUSTOM_PACKAGES, file=f)
            print("CUSTOM_VEHICLES =", CUSTOM_VEHICLES, file=f)
            print("SCENARIO_JSON =", scenario_json, file=f)

        # Run simulation with scenario JSON
        print("SCENARIO_JSON =", scenario_json)
        result = run_with_json(scenario_json)
        print("RESULT:", result)
        return jsonify({"status": "ok", "result": result})

    except Exception as e:
        import traceback
        with open("model_log.txt", "a") as f:
            f.write("Error occurred:\n")
            traceback.print_exc(file=f)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(port=6000, debug=True)
