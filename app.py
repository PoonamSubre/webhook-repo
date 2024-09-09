from flask import Flask, request, jsonify
from pymongo import MongoClient
import datetime

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client.github_events
events_collection = db.events

@app.route("/webhook", methods=["POST"])
def webhook():
    """Endpoint to receive GitHub Webhooks"""
    data = request.json
    
    # Extract relevant fields based on event type
    if 'pusher' in data:
        event_type = 'push'
        author = data['pusher']['name']
        branch = data['ref'].split('/')[-1]
        timestamp = datetime.datetime.utcnow()

        event = {
            "event_type": event_type,
            "author": author,
            "to_branch": branch,
            "timestamp": timestamp
        }
        events_collection.insert_one(event)
        return jsonify({"message": "Push event stored!"}), 200

    elif 'pull_request' in data:
        event_type = 'pull_request'
        author = data['pull_request']['user']['login']
        from_branch = data['pull_request']['head']['ref']
        to_branch = data['pull_request']['base']['ref']
        timestamp = datetime.datetime.utcnow()

        event = {
            "event_type": event_type,
            "author": author,
            "from_branch": from_branch,
            "to_branch": to_branch,
            "timestamp": timestamp
        }
        events_collection.insert_one(event)
        return jsonify({"message": "Pull request event stored!"}), 200
    
    # Handle other events (Merge) - Optional
    return jsonify({"message": "Event not handled!"}), 400

if __name__ == "__main__":
    app.run(debug=True)
