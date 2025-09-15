import json
import argparse
import sys
import utils


# Assumes your optimizer class is in 'optimizer.py'.
# Change this if you placed the LogisticsOptimizer in a different file (e.g., from agent import LogisticsOptimizer)
try:
    from inference import LogisticsOptimizer
except ImportError:
    print("Error: Could not find the 'LogisticsOptimizer' class.")
    print("Please ensure it is in a file named 'inference.py' or update the import statement in test.py.")
    sys.exit(1)


def pretty_print_results(result: dict):
    """Formats and prints the optimization results in a readable way."""
    
    print("\n" + "="*25)
    print("  OPTIMIZATION COMPLETE")
    print("="*25 + "\n")

    # --- Metrics Summary ---
    print("📊 METRICS SUMMARY")
    print("-"*25)
    metrics = result.get("metrics", {})
    success = "✅ SUCCESS" if result.get("success") else "❌ FAILED"
    print(f"  Overall Status: {success}")
    print(f"  Delivery Rate:  {metrics.get('delivery_rate', 0) * 100:.1f}% ({metrics.get('packages_delivered', 0)}/{metrics.get('total_packages', 0)})")
    print(f"  Total Time:     {metrics.get('total_time', 0):.2f} units")
    print(f"  Total Distance: {metrics.get('total_distance', 0):.2f} km")
    print(f"  Total Cost:     ${metrics.get('total_cost', 0):.2f}")
    print(f"  Vehicles Used:  {metrics.get('vehicles_used', 0)}")
    print("-"*25 + "\n")

    # --- Execution Plan ---
    print("🚛 EXECUTION PLAN (Timeline)")
    print("-"*25)
    plan = result.get("execution_plan", [])
    if not plan:
        print("  No actions were taken.")
    else:
        for step in plan:
            time = step['time']
            v_id = step['vehicle_id']
            action = step['action']
            
            if action == 'move_to':
                dest = step['destination']
                print(f"  [T={time:<6.1f}] Vehicle {v_id} -> Moves to {dest}")
                if step.get('deliveries'):
                    print(f"    {'':<10} ✔️  Delivers packages: {step['deliveries']}")
                if step.get('pickups'):
                    print(f"    {'':<10} 📦 Picks up packages: {step['pickups']}")
            elif action == 'wait':
                duration = step['duration']
                print(f"  [T={time:<6.1f}] Vehicle {v_id} -> Waits for {duration} units")
    print("-"*25 + "\n")

    # --- Vehicle Routes ---
    print("🗺️ FINAL VEHICLE ROUTES")
    print("-"*25)
    routes = result.get("vehicle_routes", {})
    if not routes:
        print("  No vehicle routes were generated.")
    else:
        for v_id, route_list in routes.items():
            route_str = " -> ".join(route_list)
            print(f"  Vehicle {v_id}: {route_str}")
    print("-"*25 + "\n")
    
    # --- Undelivered Packages ---
    undelivered = result.get("undelivered_packages", [])
    if undelivered:
        print("⚠️ UNDELIVERED PACKAGES")
        print("-"*25)
        print(f"  The following package IDs were not delivered: {undelivered}")
        print("-"*25 + "\n")


import json
from inference import LogisticsOptimizer
#from utils import pretty_print_results  # adjust import if needed

def run_with_json(scenario_data, model_path="logistics_model_v3.weights.h5"):
    """
    Run optimization directly with a scenario JSON (dict).
    
    :param scenario_data: Python dict representing the scenario.
    :param model_path: Path to trained model weights.
    :return: optimization result (dict).
    """
    # --- Load Model ---
    try:
        print(f"Loading model from '{model_path}'...")
        optimizer = LogisticsOptimizer(model_path=model_path)
    except Exception as e:
        raise RuntimeError(f"Could not load the model: {e}")

    # --- Run Optimization ---
    print("Running optimization...")
    result = optimizer.optimize_routes(scenario_data)

    # --- Print Results ---
    #pretty_print_results(result)
    utils.pretty_print_results(result)
    return result


import logging
from datetime import datetime

# --- Setup logging ---
log_filename = f"optimizer_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_filename, mode="w"),
        logging.StreamHandler()   # keeps printing to console too
    ]
)

# Redirect print -> logging
print = lambda *args, **kwargs: logging.info(" ".join(map(str, args)))


def run_with_json(scenario_data, model_path="logistics_model_v3.weights.h5"):
    """
    Run the logistics optimizer with a JSON dict (not a file).
    """
    print("data:", scenario_data)
    try:
        print(f"Loading model from '{model_path}'...")
        optimizer = LogisticsOptimizer(model_path=model_path)
    except Exception as e:
        logging.error(f"Could not load model weights from '{model_path}'. Error: {e}")
        return {"error": str(e)}

    # Run optimization
    print("Running optimization...")
    result = optimizer.optimize_routes(scenario_data)

    # Pretty print results
    try:
        pretty_print_results(result)
    except Exception as e:
        logging.warning(f"Pretty print failed: {e}")

    return result


if __name__ == "__main__":
    # Example usage if running standalone
    import json
    scenario_file = "custom_scenario.json"

    try:
        with open(scenario_file, "r") as f:
            scenario_data = json.load(f)
    except Exception as e:
        logging.error(f"Failed to load scenario file '{scenario_file}': {e}")
        sys.exit(1)

    run_with_json(scenario_data)
