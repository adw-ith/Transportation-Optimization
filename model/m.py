import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from collections import deque
import random
import json
from dataclasses import dataclass, field, asdict
from typing import List, Tuple, Dict, Any
import pickle

# ========================= DATA CLASSES =========================


# ========================= IMPROVED ENVIRONMENT =========================


# ========================= IMPROVED DQN AGENT =========================



# ========================= TRAINING FUNCTION =========================

def train_model(episodes=3000, save_path="improved_logistics_model"):
    """Train the improved logistics model"""
    
    # Create environment
    env = ImprovedLogisticsEnvironment()
    
    # Create agent
    agent = ImprovedDQNAgent(env.state_size, env.action_space_size)
    
    # Training history
    history = {
        'episode': [],
        'total_reward': [],
        'packages_delivered': [],
        'completion_time': [],
        'total_distance': [],
        'epsilon': []
    }
    
    print("Starting training...")
    print(f"State size: {env.state_size}, Action size: {env.action_space_size}")
    
    for episode in range(episodes):
        # Generate random scenario for training
        locations, routes, packages, vehicles = generate_random_scenario()
        
        # Load scenario
        state = env.load_scenario(locations, routes, packages, vehicles)
        
        total_reward = 0
        done = False
        steps = 0
        
        while not done and steps < 1000:
            # Get valid actions
            mask = env.get_valid_actions_mask()
            
            # Choose action
            action = agent.act(state, mask)
            
            # Execute action
            next_state, reward, done, info = env.step(action)
            next_mask = env.get_valid_actions_mask()
            
            # Store experience
            agent.remember(state, action, reward, next_state, done, mask, next_mask)
            
            # Update state
            state = next_state
            total_reward += reward
            steps += 1
            
            # Train
            if len(agent.memory) > agent.batch_size:
                agent.replay()
        
        # Record history
        history['episode'].append(episode)
        history['total_reward'].append(total_reward)
        history['packages_delivered'].append(env.packages_delivered)
        history['completion_time'].append(env.current_time)
        history['total_distance'].append(env.total_distance)
        history['epsilon'].append(agent.epsilon)
        
        
        avg_reward = np.mean(history['total_reward'][-100:]) if len(history['total_reward']) >= 100 else total_reward
        avg_delivered = np.mean(history['packages_delivered'][-100:]) if len(history['packages_delivered']) >= 100 else env.packages_delivered
        print(f"Episode {episode}/{episodes}")
        print(f"  Avg Reward: {avg_reward:.2f}")
        print(f"  Avg Packages Delivered: {avg_delivered:.2f}/{len(packages)}")
        print(f"  Epsilon: {agent.epsilon:.4f}")
        print()
    
    # Save model
    agent.save(save_path)
    
    # Save training history
    with open(f"{save_path}_history.pkl", 'wb') as f:
        pickle.dump(history, f)
    
    print("Training completed!")
    return agent, history

def generate_random_scenario():
    """Generate a random scenario for training"""
    
    # Random locations
    num_locations = random.randint(5, 15)
    locations = [f"Location_{i}" for i in range(num_locations)]
    
    # Random routes (ensure connectivity)
    routes = []
    for i in range(num_locations):
        for j in range(i + 1, min(i + 4, num_locations)):
            if random.random() < 0.7:  # 70% chance of connection
                distance = random.uniform(5, 50)
                routes.append(Route(locations[i], locations[j], distance))
    
    # Ensure full connectivity
    for i in range(num_locations - 1):
        route_exists = any(
            (r.start_location == locations[i] and r.end_location == locations[i + 1]) or
            (r.start_location == locations[i + 1] and r.end_location == locations[i])
            for r in routes
        )
        if not route_exists:
            routes.append(Route(locations[i], locations[i + 1], random.uniform(10, 30)))
    
    # Random packages
    num_packages = random.randint(5, 20)
    packages = []
    for i in range(num_packages):
        pickup = random.choice(locations)
        delivery = random.choice([loc for loc in locations if loc != pickup])
        packages.append(Package(
            id=i,
            pickup_location=pickup,
            delivery_location=delivery,
            weight=random.uniform(1, 15),
            priority=random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]
        ))
    
    # Random vehicles
    num_vehicles = random.randint(2, 5)
    vehicles = []
    for i in range(num_vehicles):
        vehicles.append(Vehicle(
            id=i,
            capacity=random.uniform(30, 60),
            current_location=random.choice(locations),
            speed=random.uniform(0.8, 1.5),
            cost_per_km=random.uniform(0.5, 2.0)
        ))
        vehicles[-1].current_capacity = vehicles[-1].capacity
    
    return locations, routes, packages, vehicles

# ========================= INFERENCE CLASS =========================


def example_usage():
    """Example of how to use the model"""
    
    # Example scenario
    scenario = {
        "locations": ["Warehouse", "Store_A", "Store_B", "Store_C", "Hub"],
        "routes": [
            {"start": "Warehouse", "end": "Hub", "distance": 20},
            {"start": "Hub", "end": "Store_A", "distance": 15},
            {"start": "Hub", "end": "Store_B", "distance": 12},
            {"start": "Store_A", "end": "Store_B", "distance": 8},
            {"start": "Store_B", "end": "Store_C", "distance": 10},
            {"start": "Store_C", "end": "Warehouse", "distance": 25}
        ],
        "packages": [
            {"id": 1, "pickup": "Warehouse", "delivery": "Store_A", "weight": 5, "priority": 2},
            {"id": 2, "pickup": "Warehouse", "delivery": "Store_B", "weight": 8, "priority": 1},
            {"id": 3, "pickup": "Store_A", "delivery": "Store_C", "weight": 3, "priority": 3},
            {"id": 4, "pickup": "Hub", "delivery": "Store_B", "weight": 6, "priority": 1},
            {"id": 5, "pickup": "Store_B", "delivery": "Warehouse", "weight": 4, "priority": 2}
        ],
        "vehicles": [
            {"id": 1, "capacity": 20, "location": "Warehouse", "speed": 1.0, "cost_per_km": 1.5},
            {"id": 2, "capacity": 15, "location": "Hub", "speed": 1.2, "cost_per_km": 1.2}
        ]
    }
    
    # Initialize optimizer
    optimizer = LogisticsOptimizer("improved_logistics_model")
    
    # Optimize routes
    result = optimizer.optimize_routes(scenario)
    
    # Print results
    print("\n=== OPTIMIZATION RESULTS ===")
    print(f"Success: {result['success']}")
    print(f"\nMetrics:")
    print(f"  Total Time: {result['metrics']['total_time']:.2f}")
    print(f"  Total Distance: {result['metrics']['total_distance']:.2f}")
    print(f"  Total Cost: ${result['metrics']['total_cost']:.2f}")
    print(f"  Delivery Rate: {result['metrics']['delivery_rate']*100:.1f}%")
    
    print(f"\nExecution Plan:")
    for step in result['execution_plan'][:10]:  # Show first 10 steps
        if step['action'] == 'move_to':
            print(f"  Time {step['time']:.1f}: Vehicle {step['vehicle_id']} -> {step['destination']}")
            if step['pickups']:
                print(f"    Picked up packages: {step['pickups']}")
            if step['deliveries']:
                print(f"    Delivered packages: {step['deliveries']}")
    
    print(f"\nVehicle Routes:")
    for vehicle_id, route in result['vehicle_routes'].items():
        print(f"  Vehicle {vehicle_id}: {' -> '.join(route)}")
    
    if result['undelivered_packages']:
        print(f"\nUndelivered Packages: {result['undelivered_packages']}")
    
    return result

# ========================= MAIN EXECUTION =========================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "train":
        # Train the model
        print("Training new model...")
        agent, history = train_model(episodes=2000)
        print("Model saved to 'improved_logistics_model'")
        
    elif len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test with example
        print("Testing with example scenario...")
        result = example_usage()
        
    else:
        print("Usage:")
        print("  python script.py train    # Train new model")
        print("  python script.py test     # Test with example scenario")
        print("\nFor custom usage, import LogisticsOptimizer class")