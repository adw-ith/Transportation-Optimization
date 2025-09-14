# model/app.py
from flask import Flask, request, jsonify
from test import run_simulation
from train import Package, Vehicle, Route  # use your classes
app = Flask(__name__)

@app.route("/solve", methods=["POST"])
def solve():
    try:
        data = request.get_json(force=True)
        # --- Extract arrays from backend payload ---
        locations = data.get("LOCATIONS", [])

        routes = [
            Route(r["start"], r["end"], r["distance"])
            for r in data.get("ROUTES", [])
        ]

        custom_packages = [
            Package(
                id=p["id"],
                pickup_location=p["pickup_location"],
                delivery_location=p["delivery_location"],
                weight=p["weight"],
                status=p.get("status", 0)
            )
            for p in data.get("CUSTOM_PACKAGES", [])
        ]

        custom_vehicles = [
            Vehicle(
                id=v["id"],
                capacity=v["capacity"],
                current_location=v["current_location"],
                speed=v.get("speed", 1.0),
                cost_per_km=v.get("cost_per_km", 1.0),
                available_at_time=v.get("available_at_time", 0),
            )
            for v in data.get("CUSTOM_VEHICLES", [])
        ]

        # Log to file for debugging
        with open("model_log.txt", "a") as f:
            print("locations =", locations, "routes =", routes,
                  "packages =", custom_packages, "vehicles =", custom_vehicles, file=f)

        result = run_simulation(locations, routes, custom_packages, custom_vehicles, headless=True)

        return jsonify({"status": "ok", "result": result})
    except Exception as e:
        import traceback
        # Write error details into file
        with open("model_log.txt", "a") as f:
            f.write("Error occurred:\n")
            traceback.print_exc(file=f)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(port=6000, debug=True)
