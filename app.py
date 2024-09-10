from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from datetime import datetime, timezone  # Import timezone
import json

app = Flask(__name__)

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['github_events']
events_collection = db['events']

# Webhook receiver route for GitHub
@app.route('/webhook', methods=['POST'])
def github_webhook():
    if request.method == 'POST':
        try:
            data = request.get_json()
            if data is None:
                data = json.loads(request.data)
        except Exception as e:
            return jsonify({"error": str(e)}), 400

        action_type = request.headers.get('X-GitHub-Event')

        # Handle PUSH event
        if action_type == 'push':
            event = {
                "request_id": data.get('after'),  # Git commit hash
                "author": data.get('pusher', {}).get('name'),
                "action": "PUSH",
                "from_branch": None,  # Not needed for PUSH
                "to_branch": data.get('ref', '').split('/')[-1],
                "timestamp": datetime.now(timezone.utc).isoformat()  # Updated to use timezone-aware datetime
            }
            events_collection.insert_one(event)

        # Handle PULL_REQUEST event
        elif action_type == 'pull_request':
            pr_action = data.get('action')
            if pr_action in ["opened", "closed"]:
                event = {
                    "request_id": data.get('pull_request', {}).get('id'),
                    "author": data.get('pull_request', {}).get('user', {}).get('login'),
                    "action": "PULL_REQUEST",
                    "from_branch": data.get('pull_request', {}).get('head', {}).get('ref'),
                    "to_branch": data.get('pull_request', {}).get('base', {}).get('ref'),
                    "timestamp": datetime.now(timezone.utc).isoformat()  # Updated to use timezone-aware datetime
                }
                events_collection.insert_one(event)

            # Handle MERGE event within PULL_REQUEST event
            if data.get('pull_request', {}).get('merged', False):
                event = {
                    "request_id": data.get('pull_request', {}).get('id'),
                    "author": data.get('pull_request', {}).get('user', {}).get('login'),
                    "action": "MERGE",
                    "from_branch": data.get('pull_request', {}).get('head', {}).get('ref'),
                    "to_branch": data.get('pull_request', {}).get('base', {}).get('ref'),
                    "timestamp": datetime.now(timezone.utc).isoformat()  # Updated to use timezone-aware datetime
                }
                events_collection.insert_one(event)

        return jsonify({"status": "success"}), 200

# Fetch latest events for the UI
@app.route('/events', methods=['GET'])
def get_events():
    events = list(events_collection.find().sort('timestamp', -1).limit(10))  # Get the latest 10 events
    for event in events:
        event['_id'] = str(event['_id'])  # Convert ObjectId to string
    return jsonify(events), 200

# Serve the frontend UI
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
