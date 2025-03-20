from flask import Flask, request, jsonify, send_from_directory
from tinydb import TinyDB, Query
from flask_mail import Mail, Message
import datetime
import google.generativeai as genai
import os

genai.configure(api_key="AIzaSyCYSQD0AhA7xN1dojqxCWOfw1zmiwMlaJk")

app = Flask(__name__)
db = TinyDB('bills.json')

# Configure Flask-Mail (Update with actual credentials if needed)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_password'
mail = Mail(app)

# Serve the HTML file
@app.route('/')
def serve_index():
    return send_from_directory(os.getcwd(), 'index.html')

# Add a new bill
@app.route('/bills', methods=['POST'])
def add_bill():
    data = request.json
    data['due_date'] = str(data['due_date'])  # Convert date to string for JSON storage
    db.insert(data)
    return jsonify({"message": "Bill added successfully!"}), 201

# Get all bills
@app.route('/bills', methods=['GET'])
def get_bills():
    return jsonify(db.all())

# Get a single bill by ID
@app.route('/bills/<int:bill_id>', methods=['GET'])
def get_bill(bill_id):
    Bill = Query()
    result = db.get(Bill.id == bill_id)
    return jsonify(result) if result else (jsonify({"message": "Bill not found"}), 404)

# Update a bill
@app.route('/bills/<int:bill_id>', methods=['PUT'])
def update_bill(bill_id):
    Bill = Query()
    data = request.json
    db.update(data, Bill.id == bill_id)
    return jsonify({"message": "Bill updated successfully!"})

# Delete a bill
@app.route('/bills', methods=['DELETE'])
def delete_bill():
    bill_id = request.args.get('id')
    db.remove(Query().id == int(bill_id))
    return jsonify({'message': 'Bill deleted'}), 200

# Send email reminder
@app.route('/send-reminder', methods=['POST'])
def send_reminder():
    data = request.json
    email = data.get('email')
    bill_name = data.get('bill_name')
    due_date = data.get('due_date')
    
    msg = Message(f"Reminder: {bill_name} is due soon!", sender='your_email@gmail.com', recipients=[email])
    msg.body = f"Your bill '{bill_name}' is due on {due_date}. Please make the payment on time."
    mail.send(msg)
    
    return jsonify({"message": "Reminder email sent successfully!"})

# Get reminders for upcoming due dates
@app.route('/reminders', methods=['GET'])
def get_reminders():
    today = datetime.date.today()
    upcoming_bills = [bill for bill in db.all() if datetime.datetime.strptime(bill['due_date'], '%Y-%m-%d').date() >= today]
    return jsonify(upcoming_bills)

# Get AI-powered insights
@app.route('/insights', methods=['GET'])
def get_insights():
    bills = db.all()
    total_spent = sum(bill['amount'] for bill in bills)
    frequent_services = [bill['bill_name'] for bill in bills if bill['amount'] > 10]

    # Gemini API Call
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(
        f"I spend {total_spent} on these services: {frequent_services}. Suggest free alternatives."
    )

    suggestions = response.text if response.text else "No suggestions available."

    return jsonify({
        "total_spent": total_spent,
        "frequent_services": frequent_services,
        "suggestions": suggestions
    })

# AI Query Endpoint
@app.route('/ai-query', methods=['POST'])
def ai_query():
    data = request.json
    user_query = data.get('query')

    # Fetch all bills from the database
    bills = db.all()
    
    # Prepare a summary of the bills for the AI model
    bill_summary = [{"name": bill['bill_name'], "amount": bill['amount'], "due_date": bill['due_date']} for bill in bills]

    # Call the AI model to get a response
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(
        f"User query: {user_query}\n\nHere are the current bills:\n{bill_summary}\n\nPlease provide a relevant response."
    )

    ai_response = response.text if response.text else "I'm sorry, I couldn't generate a response."

    return jsonify({"response": ai_response, "bills": bill_summary})

if __name__ == '__main__':
    app.run(debug=True)
