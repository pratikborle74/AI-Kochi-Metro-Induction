import json
import os
import heapq
from collections import deque

# The path to our data file (updated for local integration)
DEPOT_FILE_PATH = 'muttom_yard.json'

def load_depot():
    """Loads the depot data from the JSON file."""
    try:
        with open(DEPOT_FILE_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": "Depot data file not found."}
    except json.JSONDecodeError:
        return {"error": "Error decoding the depot JSON file."}

def save_depot(depot_data):
    """Saves the updated depot data back to the JSON file."""
    try:
        with open(DEPOT_FILE_PATH, 'w') as f:
            json.dump(depot_data, f, indent=2)
        return {"success": "Depot data saved."}
    except Exception as e:
        return {"error": str(e)}

def update_track_status(track_id, new_status):
    """Finds a track by its ID and updates its status."""
    depot_data = load_depot()
    if "error" in depot_data:
        return depot_data

    track_found = False
    for track in depot_data.get("tracks", []):
        if track.get("trackId") == track_id:
            track["status"] = new_status
            track_found = True
            break
    
    if not track_found:
        return {"error": f"Track with ID '{track_id}' not found."}
    
    save_result = save_depot(depot_data)
    if "error" in save_result:
        return save_result
        
    return {"success": f"Status of track '{track_id}' updated to '{new_status}'."}

def create_new_depot(depot_data):
    """Creates a new depot JSON file."""
    if "depotId" not in depot_data:
        return {"error": "Missing 'depotId' in the provided data."}

    depot_id = depot_data["depotId"]
    filename = f"{depot_id}.json"
    new_file_path = filename  # Store in current directory for integration

    if os.path.exists(new_file_path):
        return {"error": f"Depot with ID '{depot_id}' already exists."}

    try:
        with open(new_file_path, 'w') as f:
            json.dump(depot_data, f, indent=2)
        return {"success": f"New depot '{depot_id}' created successfully."}
    except Exception as e:
        return {"error": str(e)}

def find_path(depot_data, start_track_id, end_track_id):
    """Finds the shortest path from a start track to an end track using BFS."""
    graph = {}
    for switch in depot_data.get("switches", []):
        connections = switch.get("connectsTracks", [])
        for track_id in connections:
            if track_id not in graph:
                graph[track_id] = []
            for other_track_id in connections:
                if track_id != other_track_id:
                    graph[track_id].append((switch["switchId"], other_track_id))

    if start_track_id not in graph or end_track_id not in graph:
        return None

    queue = deque([(start_track_id, [start_track_id])])
    visited = {start_track_id}

    while queue:
        current_track, path = queue.popleft()
        if current_track == end_track_id:
            return path
        for switch_id, neighbor_track in graph.get(current_track, []):
            if neighbor_track not in visited:
                visited.add(neighbor_track)
                new_path = path + [switch_id, neighbor_track]
                queue.append((neighbor_track, new_path))
    
    return None

def find_efficient_path(depot_data, start_track_id, end_track_id):
    """
    Finds the most energy-efficient (lowest cost) path using Dijkstra's algorithm.
    The "cost" is the distance in metres.
    """
    graph = {}
    track_map = {track['trackId']: track for track in depot_data.get("tracks", [])}

    for switch in depot_data.get("switches", []):
        connections = switch.get("connectsTracks", [])
        for track_id in connections:
            if track_id not in graph:
                graph[track_id] = []
            
            # Use distance_metres as the cost for traversal
            cost = track_map.get(track_id, {}).get("distance_metres", 1) 

            for other_track_id in connections:
                if track_id != other_track_id:
                    graph[track_id].append((cost, other_track_id, switch["switchId"]))

    if start_track_id not in graph or end_track_id not in graph:
        return None

    priority_queue = [(0, start_track_id, [start_track_id])]
    visited_costs = {start_track_id: 0}

    while priority_queue:
        total_cost, current_track, path = heapq.heappop(priority_queue)

        if total_cost > visited_costs[current_track]:
            continue
        
        if current_track == end_track_id:
            return {"path": path, "total_cost_metres": total_cost}

        for cost, neighbor_track, switch_id in graph.get(current_track, []):
            new_cost = total_cost + cost
            if new_cost < visited_costs.get(neighbor_track, float('inf')):
                visited_costs[neighbor_track] = new_cost
                new_path = path + [switch_id, neighbor_track]
                heapq.heappush(priority_queue, (new_cost, neighbor_track, new_path))
                
    return None

def delete_depot(depot_id):
    """Deletes a depot's JSON file by its ID."""
    filename = f"{depot_id}.json"
    file_path = filename  # Use current directory for integration

    if not os.path.exists(file_path):
        return {"error": f"Depot with ID '{depot_id}' not found."}

    try:
        os.remove(file_path)
        return {"success": f"Depot '{depot_id}' deleted successfully."}
    except Exception as e:
        return {"error": str(e)}