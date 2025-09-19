from flask import Flask, jsonify, request
from backend.digital_twin import depot_manager

# Initialize the Flask app
app = Flask(__name__)

@app.route('/api/depot/muttom', methods=['GET'])
def get_muttom_depot():
    """API endpoint to get the full status of the Muttom depot."""
    depot_data = depot_manager.load_depot()
    if "error" in depot_data:
        return jsonify(depot_data), 500
    return jsonify(depot_data)

@app.route('/api/depot/muttom/available_tracks', methods=['GET'])
def get_available_tracks_endpoint():
    """API endpoint to get only the available tracks."""
    depot_data = depot_manager.load_depot()
    if "error" in depot_data:
        return jsonify(depot_data), 500
    
    available_tracks = depot_manager.get_available_tracks(depot_data)
    return jsonify(available_tracks)

@app.route('/api/depot/muttom/track/<string:track_id>', methods=['PUT'])
def update_track(track_id):
    """API endpoint to update the status of a specific track."""
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({"error": "Missing 'status' in request body."}), 400

    new_status = data['status']
    result = depot_manager.update_track_status(track_id, new_status)
    
    if "error" in result:
        return jsonify(result), 404
    
    return jsonify(result)

@app.route('/api/depot', methods=['POST'])
def create_depot():
    """API endpoint to create a new depot."""
    depot_data = request.get_json()
    if not depot_data:
        return jsonify({"error": "No data provided in request body."}), 400

    result = depot_manager.create_new_depot(depot_data)
    
    if "error" in result:
        return jsonify(result), 409
    
    return jsonify(result), 201

# --- NEW ENDPOINT ---
@app.route('/api/depot/muttom/path', methods=['GET'])
def get_efficient_path_endpoint():
    """
    API endpoint to find the most energy-efficient path between two tracks.
    Requires 'start' and 'end' query parameters.
    Example: /api/depot/muttom/path?start=SL-01&end=WB-01
    """
    start_track = request.args.get('start')
    end_track = request.args.get('end')

    if not start_track or not end_track:
        return jsonify({"error": "Please provide both 'start' and 'end' query parameters."}), 400

    depot_data = depot_manager.load_depot()
    if "error" in depot_data:
        return jsonify(depot_data), 500

    path_info = depot_manager.find_efficient_path(depot_data, start_track, end_track)

    if path_info:
        return jsonify(path_info)
    else:
        return jsonify({"error": f"No path found between '{start_track}' and '{end_track}'."}), 404
    
@app.route('/api/depot/<string:depot_id>', methods=['DELETE'])
def delete_depot_endpoint(depot_id):
    """API endpoint to delete a depot."""
    result = depot_manager.delete_depot(depot_id)
    
    if "error" in result:
        return jsonify(result), 404 # 404 Not Found is the correct status
    
    return jsonify(result)
