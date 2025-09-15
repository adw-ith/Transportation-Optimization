import streamlit as st
from streamlit_folium import st_folium
import folium
import requests
import os
from dotenv import load_dotenv

st.set_page_config(layout="wide")

# --- Sidebar/Left Panel ---
st.markdown("""
<style>
[data-testid="stSidebar"] {width: 400px !important;}
</style>
""", unsafe_allow_html=True)

# --- Helper: Geocode ---
def geocode_location(location_name):
    url = f"https://nominatim.openstreetmap.org/search"
    params = {"q": location_name, "format": "json", "limit": 1}
    try:
        resp = requests.get(url, params=params, headers={"User-Agent": "genai-routing-app"})
        if resp.status_code == 200 and resp.json():
            data = resp.json()[0]
            return [float(data['lat']), float(data['lon'])]
    except Exception:
        pass
    return None

load_dotenv()
ORS_API_KEY = os.getenv("ORS_API_KEY")

# --- Helper: Get route from ORS ---
def get_route(src_coords, dest_coords, mode):
    mode_map = {"Car": "driving-car", "Bike": "cycling-regular", "Bus": "driving-hgv", "Walk": "foot-walking"}
    profile = mode_map.get(mode, "driving-car")
    url = f"https://api.openrouteservice.org/v2/directions/{profile}"
    headers = {"Authorization": ORS_API_KEY, "Content-Type": "application/json"}
    body = {
        "coordinates": [
            [src_coords[1], src_coords[0]],  # ORS expects [lng, lat]
            [dest_coords[1], dest_coords[0]]
        ]
    }
    try:
        resp = requests.post(url, json=body, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            coords = data['features'][0]['geometry']['coordinates']
            # Convert to [lat, lng] for folium
            return [[lat, lng] for lng, lat in coords]
    except Exception:
        pass
    return None

# --- Main Layout ---
col1, col2 = st.columns([1,2])

with col1:
    st.markdown("## Route Assistant")
    tab1, tab2 = st.tabs(["Planner", "Chat"])
    with tab1:
        if 'destinations' not in st.session_state:
            st.session_state['destinations'] = ['']
        if 'loads' not in st.session_state:
            st.session_state['loads'] = [0]
        with st.form("route_form"):
            source = st.text_input("SOURCE", placeholder="123 Main St, New York")
            dest_cols = st.columns([3,2,1])
            destinations = []
            loads = []
            for i in range(len(st.session_state['destinations'])):
                with dest_cols[0]:
                    dest = st.text_input(f"DESTINATION {i+1}", value=st.session_state['destinations'][i], key=f"dest_{i}")
                with dest_cols[1]:
                    load = st.number_input(f"Load (kg) {i+1}", min_value=0, value=st.session_state['loads'][i], key=f"load_{i}")
                destinations.append(dest)
                loads.append(load)
            with dest_cols[2]:
                if st.form_submit_button("Add Destination"):
                    st.session_state['destinations'].append('')
                    st.session_state['loads'].append(0)
                    st.rerun()
            vehicle_capacity = st.number_input("Vehicle Capacity (kg)", min_value=1, value=1000)
            transport = st.radio("TRANSPORT", ["Car", "Bike", "Bus", "Walk"], horizontal=True)
            submitted = st.form_submit_button("Get Directions")
        if submitted:
            st.session_state['source'] = source
            st.session_state['destinations'] = destinations
            st.session_state['loads'] = loads
            st.session_state['vehicle_capacity'] = vehicle_capacity
            st.session_state['transport'] = transport
            # Geocode
            src_coords = geocode_location(source)
            dest_coords_list = [geocode_location(dest) for dest in destinations if dest]
            st.session_state['src_coords'] = src_coords
            st.session_state['dest_coords_list'] = dest_coords_list
            # Get route for each leg
            route = []
            if src_coords and dest_coords_list:
                prev = src_coords
                for dest in dest_coords_list:
                    leg = get_route(prev, dest, transport)
                    if leg:
                        if not route:
                            route.extend(leg)
                        else:
                            route.extend(leg[1:])  # avoid duplicate point
                        prev = dest
                st.session_state['route_polyline'] = route
            # Prepare JSON for backend
            backend_json = {
                "source": source,
                "source_coords": src_coords,
                "destinations": destinations,
                "destination_coords": dest_coords_list,
                "loads": loads,
                "vehicle_type": transport,
                "vehicle_capacity": vehicle_capacity
            }
            st.session_state['backend_json'] = backend_json
            st.success("Route and data ready!")
            st.json(backend_json)
            print("Chat backend_json:", backend_json)
            resp = requests.post("http://localhost:5000/optimize", json=backend_json)
            print("Backend response:", resp.json())

    with tab2:
        st.markdown("### Chat with Route Assistant")
        if 'chat_history' not in st.session_state:
            st.session_state['chat_history'] = []
        user_msg = st.text_input("You:", key="chat_input")
        if st.button("Send", key="chat_send") and user_msg:
            st.session_state['chat_history'].append(("user", user_msg))
            # Call GenAI API
            with st.spinner("Thinking..."):
                resp = requests.post('http://localhost:5005/parse', json={'query': user_msg})
                if resp.status_code == 200:
                    ai_msg = resp.json()
                    st.session_state['chat_history'].append(("assistant", ai_msg))
                    # Show raw Gemini response for debugging
                    st.markdown("**Raw Gemini response:**")
                    st.json(ai_msg)
                    # Parse and use Gemini result
                    source = ai_msg.get('source', '')
                    destinations = ai_msg.get('destinations', [])
                    loads = ai_msg.get('loads', [])
                    vehicle_type = ai_msg.get('vehicle', {}).get('type', ai_msg.get('vehicle_type', 'Car'))
                    vehicle_capacity = ai_msg.get('vehicle', {}).get('capacity', ai_msg.get('vehicle_capacity', 1000))
                    # Show parsed fields for debugging
                    st.markdown(f"**Parsed source:** {source}")
                    st.markdown(f"**Parsed destinations:** {destinations}")
                    st.markdown(f"**Parsed loads:** {loads}")
                    st.markdown(f"**Parsed vehicle_type:** {vehicle_type}")
                    st.markdown(f"**Parsed vehicle_capacity:** {vehicle_capacity}")
                    # Geocode
                    src_coords = geocode_location(source) if source else None
                    dest_coords_list = [geocode_location(dest) for dest in destinations if dest]
                    if not source or not destinations:
                        st.warning("Gemini did not parse source or destinations. Please rephrase your prompt.")
                    elif not src_coords or not dest_coords_list:
                        st.warning("Could not geocode source or destinations. Please check the parsed locations.")
                    else:
                        st.session_state['src_coords'] = src_coords
                        st.session_state['dest_coords_list'] = dest_coords_list
                        st.session_state['source'] = source
                        st.session_state['destinations'] = destinations
                        st.session_state['loads'] = loads
                        st.session_state['vehicle_capacity'] = vehicle_capacity
                        st.session_state['transport'] = vehicle_type
                        # Get route for each leg
                        route = []
                        prev = src_coords
                        for dest in dest_coords_list:
                            leg = get_route(prev, dest, vehicle_type)
                            if leg:
                                if not route:
                                    route.extend(leg)
                                else:
                                    route.extend(leg[1:])
                                prev = dest
                        st.session_state['route_polyline'] = route
                        # Prepare JSON for backend
                        backend_json = {
                            "source": source,
                            "source_coords": src_coords,
                            "destinations": destinations,
                            "destination_coords": dest_coords_list,
                            "loads": loads,
                            "vehicle_type": vehicle_type,
                            "vehicle_capacity": vehicle_capacity
                        }
                        st.session_state['backend_json'] = backend_json
                        st.success("Parsed and mapped!")
                        st.json(backend_json)
                        print("Chat backend_json:", backend_json)
                        resp = requests.post("http://localhost:5000/optimize", json=backend_json)
                        print("Backend response:", resp.json())

                else:
                    ai_msg = {"error": "GenAI error"}
                    st.session_state['chat_history'].append(("assistant", ai_msg))
        for role, msg in st.session_state['chat_history']:
            if role == "user":
                st.markdown(f"**You:** {msg}")
            else:
                st.markdown(f"**Assistant:** {msg}")

with col2:
    st.markdown("## Geographical Map")
    src_coords = st.session_state.get('src_coords')
    dest_coords_list = st.session_state.get('dest_coords_list', [])
    route_polyline = st.session_state.get('route_polyline')
    # Center map on source, then first destination, else default
    if src_coords:
        map_center = src_coords
    elif dest_coords_list:
        map_center = dest_coords_list[0]
    else:
        map_center = [40.75, -73.98]
    m = folium.Map(location=map_center, zoom_start=13)
    # Markers
    if src_coords:
        folium.Marker(src_coords, tooltip='Source', icon=folium.Icon(color='green')).add_to(m)
    for i, dest in enumerate(dest_coords_list):
        folium.Marker(dest, tooltip=f'Destination {i+1}', icon=folium.Icon(color='red')).add_to(m)
    # Route
    if route_polyline:
        folium.PolyLine(route_polyline, color='blue', weight=5).add_to(m)
    elif src_coords and dest_coords_list:
        folium.PolyLine([src_coords] + dest_coords_list, color='gray', weight=2, dash_array='5,10').add_to(m)
    st_folium(m, width=600, height=500, key="main_map")