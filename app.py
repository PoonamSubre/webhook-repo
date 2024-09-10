from flask import send_from_directory
from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import datetime

app = Flask(__name__)

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['github_events']
events_collection = db['events']

# Webhook receiver route for GitHub
@app.route('/webhook', methods=['POST'])
def github_webhook():
    if request.method == 'POST':
        data = request.json
        action_type = request.headers.get('X-GitHub-Event')

        # Handle PUSH event
        if action_type == 'push':
            event = {
                "request_id": data['after'],  # Git commit hash
                "author": data['pusher']['name'],
                "action": "PUSH",
                "from_branch": None,  # Not needed for PUSH
                "to_branch": data['ref'].split('/')[-1],
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
            events_collection.insert_one(event)

        # Handle PULL_REQUEST event
        elif action_type == 'pull_request':
            pr_action = data['action']
            if pr_action in ["opened", "closed"]:
                event = {
                    "request_id": data['pull_request']['id'],
                    "author": data['pull_request']['user']['login'],
                    "action": "PULL_REQUEST",
                    "from_branch": data['pull_request']['head']['ref'],
                    "to_branch": data['pull_request']['base']['ref'],
                    "timestamp": datetime.datetime.utcnow().isoformat()
                }
                events_collection.insert_one(event)

        # Handle MERGE event
        elif action_type == 'pull_request' and data['pull_request']['merged']:
            event = {
                "request_id": data['pull_request']['id'],
                "author": data['pull_request']['user']['login'],
                "action": "MERGE",
                "from_branch": data['pull_request']['head']['ref'],
                "to_branch": data['pull_request']['base']['ref'],
                "timestamp": datetime.datetime.utcnow().isoformat()
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
