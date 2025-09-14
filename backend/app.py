from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend to avoid GUI errors
import matplotlib.pyplot as plt
import networkx as nx   
import time
import traceback


app = Flask(__name__)
MODEL_URL = "http://127.0.0.1:6000/solve"   # replace with your TSP model endpoint

def prepare_and_send_to_model(backend_json, graphhopper_result, distance_matrix):
    """
    Prepare the correct payload format for the DQN model endpoint
    using a fully connected graph (from distance matrix).
    """
    print("working")

    # --- Build LOCATIONS list (named locations as strings) ---
    locations = [backend_json.get("source", "")] + backend_json.get("destinations", [])

    # --- Build ROUTES from distance matrix (fully connected graph) ---
    routes = []
    for i in range(len(locations)):
        for j in range(len(locations)):
            if i != j and distance_matrix[i][j] is not None:
                routes.append({
                    "start": locations[i],
                    "end": locations[j],
                    "distance": distance_matrix[i][j]
                })

    # --- Build CUSTOM_PACKAGES from loads ---
    packages = []
    for i, load in enumerate(backend_json.get("loads", [])):
        packages.append({
            "id": i,
            "pickup_location": backend_json.get("source", ""),
            "delivery_location": locations[i+1] if i+1 < len(locations) else locations[-1],
            "weight": load,
            "status": 0
        })

    # --- Build CUSTOM_VEHICLES ---
    vehicles = [{
        "id": 0,
        "capacity": backend_json.get("vehicle_capacity", 1000),
        "current_location": backend_json.get("source", ""),
        "speed": 1.0,
        "cost_per_km": 1.0,
        "available_at_time": 0
    }]

    payload = {
        "LOCATIONS": locations,
        "ROUTES": routes,           # now fully connected
        "CUSTOM_PACKAGES": packages,
        "CUSTOM_VEHICLES": vehicles
    }

    return payload

# Example usage after backend GraphHopper processing:
# backend_json = {...}  # your JSON from frontend
# graphhopper_result = {...}  # result from GraphHopper
# model_output = prepare_and_send_to_model(backend_json, graphhopper_result)
# print(model_output)

# --- Visualization Helpers ---
def visualize_distance_matrix_graph(locations, distance_matrix, filename="distance_matrix_graph.png"):
    plt.figure(figsize=(12, 12))
    G = nx.Graph()
    edge_labels = {}
    for i in range(len(locations)):
        for j in range(i + 1, len(locations)):
            if distance_matrix[i][j] is not None:
                G.add_edge(i, j, weight=distance_matrix[i][j])
                edge_labels[(i, j)] = f"{distance_matrix[i][j]} km"
    pos = nx.spring_layout(G, seed=42)
    nx.draw_networkx_nodes(G, pos, node_color='skyblue', node_size=700)
    nx.draw_networkx_labels(G, pos)
    nx.draw_networkx_edges(G, pos, alpha=0.5, edge_color='gray')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red', font_size=8)
    nx.draw_networkx_nodes(G, pos, nodelist=[0], node_color='green', node_size=800, label='Node 0 (Origin)')
    plt.title("Direct Routes and Distances Between All Nodes")
    plt.legend()
    plt.savefig(filename)
    plt.close()

def visualize_complete_graph(locations, distance_matrix, optimized_path, filename="optimized_route_graph.png"):
    plt.figure(figsize=(12, 12))
    G = nx.Graph()
    edge_labels = {}
    for i in range(len(locations)):
        for j in range(i + 1, len(locations)):
            if distance_matrix[i][j] is not None:
                G.add_edge(i, j, weight=distance_matrix[i][j])
                edge_labels[(i, j)] = f"{distance_matrix[i][j]} km"
    pos = nx.spring_layout(G, seed=42)
    nx.draw_networkx_nodes(G, pos, node_color='skyblue', node_size=700)
    nx.draw_networkx_labels(G, pos)
    nx.draw_networkx_edges(G, pos, alpha=0.5, edge_color='gray')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red', font_size=8)
    nx.draw_networkx_nodes(G, pos, nodelist=[optimized_path[0]], node_color='green', node_size=800, label='Origin')
    nx.draw_networkx_nodes(G, pos, nodelist=[optimized_path[-1]], node_color='red', node_size=800, label='Destination')
    route_edges = list(zip(optimized_path, optimized_path[1:]))
    nx.draw_networkx_edges(G, pos, edgelist=route_edges, edge_color='black', width=2.5, arrows=True, arrowstyle='->', arrowsize=20)
    plt.title("Complete Network Graph with Optimized Route")
    plt.legend()
    plt.savefig(filename)
    plt.close()

# --- GraphHopper Helpers ---
def get_distance_matrix_graphhopper(api_key, destinations):
    endpoint = f"https://graphhopper.com/api/1/matrix?key={api_key}"

    # Expect dicts {"lat": x, "lng": y}, GraphHopper wants [lng, lat]
    points = [[loc["lng"], loc["lat"]] for loc in destinations]

    payload = {"points": points, "out_arrays": ["distances"]}
    response = requests.post(endpoint, json=payload)
    response.raise_for_status()
    data = response.json()

    if "distances" in data:
        return [[round(d / 1000, 2) if d is not None else None for d in row] for row in data['distances']]
    return {"error": data.get('message', 'Failed to retrieve distance matrix.')}

def get_optimized_route_graphhopper(api_key, destinations):
    if len(destinations) < 2:
        return {"error": "Please provide at least two destinations."}

    endpoint = f"https://graphhopper.com/api/1/vrp?key={api_key}"

    vehicle = {
        "vehicle_id": "my_vehicle",
        "start_address": {
            "location_id": "loc_0",
            "lat": destinations[0]["lat"],
            "lon": destinations[0]["lng"]
        },
        "end_address": {
            "location_id": f"loc_{len(destinations)-1}",
            "lat": destinations[-1]["lat"],
            "lon": destinations[-1]["lng"]
        }
    }

    services = []
    for i, loc in enumerate(destinations[1:-1]):
        services.append({
            "id": str(i + 1),
            "address": {
                "location_id": f"loc_{i+1}",
                "lat": loc["lat"],
                "lon": loc["lng"]
            }
        })

    payload = {"vehicles": [vehicle], "services": services}
    response = requests.post(endpoint, json=payload)
    response.raise_for_status()
    data = response.json()

    if "solution" not in data or not data["solution"].get("routes"):
        return {"error": "No routes found. Check locations or VRP request.", "raw_response": data}

    solution = data["solution"]
    total_distance_km = round(solution["distance"] / 1000, 2)
    activities = solution["routes"][0]["activities"]

    optimized_path = []
    for activity in activities:
        if activity["type"] == "start":
            optimized_path.append(0)
        elif activity["type"] == "end":
            optimized_path.append(len(destinations) - 1)
        else:
            optimized_path.append(int(activity["id"]))

    leg_details = []
    for i in range(len(activities) - 1):
        from_node = optimized_path[i]
        to_node = optimized_path[i + 1]
        distance_km = round(activities[i+1]["distance"] / 1000, 2)
        leg_details.append({
            "from_node": from_node,
            "to_node": to_node,
            "distance_km": distance_km,
            "summary": f"Node {from_node} -> Node {to_node}"
        })

    return {"total_distance_km": total_distance_km, "optimized_path": optimized_path, "legs": leg_details}

# --- Geocoding ---
def geocode_location(place, api_key):
    url = f"https://graphhopper.com/api/1/geocode?q={place}&key={api_key}"
    resp = requests.get(url)
    resp.raise_for_status()
    results = resp.json().get("hits", [])
    if not results:
        raise ValueError(f"No results found for {place}")
    hit = results[0]
    return (hit["point"]["lat"], hit["point"]["lng"])

# --- Flask Route ---
@app.route("/optimize", methods=["POST"])
def optimize_route():
    start_ts = time.time()
    try:
        backend_json = request.get_json(force=True)

        load_dotenv()
        API_KEY = os.getenv("GRAPHHOPPER_API_KEY")
        if not API_KEY:
            return jsonify({"error": "GraphHopper API key not found"}), 500

        # --- Extract coordinates ---
        source_coords = backend_json.get("source_coords", [])
        destination_coords = backend_json.get("destination_coords", [])
        locations = []

        if source_coords and isinstance(source_coords, (list, tuple)) and len(source_coords) >= 2:
            locations.append({"lat": source_coords[0], "lng": source_coords[1]})

        for dest in destination_coords:
            if isinstance(dest, (list, tuple)) and len(dest) >= 2:
                locations.append({"lat": dest[0], "lng": dest[1]})
            elif isinstance(dest, dict) and "lat" in dest and "lng" in dest:
                locations.append({"lat": dest["lat"], "lng": dest["lng"]})

        if not locations:
            return jsonify({"error": "No valid locations provided"}), 400

        # --- Get GraphHopper results ---
        distance_matrix = get_distance_matrix_graphhopper(API_KEY, locations)
        graphhopper_result = get_optimized_route_graphhopper(API_KEY, locations)
        
        if isinstance(graphhopper_result, dict) and graphhopper_result.get("error"):
            return jsonify({"error": "GraphHopper VRP error", "detail": graphhopper_result}), 500

        # --- Prepare model payload in correct format ---
        model_payload = prepare_and_send_to_model(backend_json, graphhopper_result, distance_matrix)
        print("Prepared model payload:", model_payload)
        
        # --- Send to model ---
        try:
            model_response = requests.post(MODEL_URL, json=model_payload, timeout=30)
            model_response.raise_for_status()
            model_result = model_response.json()
        except requests.exceptions.RequestException as e:
            model_result = {"error": f"Model request failed: {str(e)}"}
        
        # --- Generate visualizations ---
        try:
            visualize_distance_matrix_graph(locations, distance_matrix)
            visualize_complete_graph(locations, distance_matrix, graphhopper_result.get("optimized_path", []))
        except Exception as viz_error:
            print(f"Visualization error: {viz_error}")

        # --- Return comprehensive response ---
        elapsed = time.time() - start_ts
        return jsonify({
            "status": "success",
            "processing_time_seconds": round(elapsed, 2),
            "locations": locations,
            "distance_matrix": distance_matrix,
            "graphhopper_result": graphhopper_result,
            "model_payload": model_payload,
            "model_result": model_result
        })

    except Exception as e:
        tb = traceback.format_exc()
        return jsonify({
            "error": "Internal server error", 
            "detail": str(e), 
            "traceback": tb
        }), 500
    


if __name__ == "__main__":
    app.run(port=5000, debug=True)
