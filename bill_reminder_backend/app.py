from flask import Flask, request, jsonify
from tinydb import TinyDB, Query

app = Flask(__name__)
db = TinyDB('db.json')  # Initialize TinyDB

@app.route('/bills', methods=['GET', 'POST', 'DELETE'])
def manage_bills():
    if request.method == 'GET':
        # Fetch all bills
        bills = db.all()
        return jsonify(bills)

    elif request.method == 'POST':
        # Add a new bill
        bill_data = request.json
        db.insert(bill_data)
        return jsonify(bill_data), 201

    elif request.method == 'DELETE':
        # Remove a bill
        bill_id = request.args.get('id')
        db.remove(Query().id == int(bill_id))
        return jsonify({'message': 'Bill deleted'}), 200

@app.route('/reminders', methods=['GET'])
def get_reminders():
    # Logic to fetch due date notifications
    return jsonify({'message': 'Reminders endpoint'})

@app.route('/suggestions', methods=['GET'])
def get_suggestions():
    # Logic to provide free alternative recommendations
    return jsonify({'message': 'Suggestions endpoint'})

if __name__ == '__main__':
    app.run(debug=True)
