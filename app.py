from flask import Flask, request, jsonify, send_from_directory
from tinydb import TinyDB, Query
from flask_mail import Mail, Message
import datetime
import google.generativeai as genai
import os
from flask_cors import CORS
import json
from dotenv import load_dotenv  # Add this import

# Load environment variables from .env file
load_dotenv()  # This loads the variables from .env

# Configure Gemini API with key from environment variables
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Warning: GEMINI_API_KEY not found in environment variables.")
genai.configure(api_key=api_key)

app = Flask(__name__)
CORS(app)
db = TinyDB('bills.json')

# Configure Flask-Mail with credentials from environment variables
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
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

# Modified AI query endpoint to better handle service recommendations
@app.route('/ai-query', methods=['POST', 'OPTIONS'])
def ai_query():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.json
        user_query = data.get('query')
        
        if not user_query:
            return jsonify({"error": "No query provided"}), 400

        # Fetch all bills from the database
        bills = db.all()
        
        # Prepare a summary of the bills for the AI model
        bill_summary = [{"name": bill['bill_name'], "amount": bill['amount'], "due_date": bill['due_date']} for bill in bills]
        
        # Check if this is a service recommendation query
        is_service_query = any(keyword in user_query.lower() for keyword in 
                               ['wifi', 'internet', 'broadband', 'streaming', 'subscription', 'suggest'])
        
        # Add service data if this is a recommendation query
        service_data = ""
        if is_service_query:
            # Sample service data - in a real app, this could come from a database or API
            services = {
                "wifi": [
                    {"name": "Jio Fiber", "cost_range": "$5-30", "features": "30-300Mbps, unlimited data"},
                    {"name": "Airtel Xstream", "cost_range": "$7-40", "features": "40-1000Mbps, unlimited data"},
                    {"name": "BSNL Fiber", "cost_range": "$4-25", "features": "20-300Mbps, data caps apply"}
                ],
                "streaming": [
                    {"name": "Netflix", "cost_range": "$10-20", "features": "Multiple screens, 4K content"},
                    {"name": "Disney+", "cost_range": "$8-12", "features": "Family content, originals"},
                    {"name": "Prime Video", "cost_range": "$9", "features": "Included with Prime membership"}
                ]
            }
            
            service_data = f"\n\nHere is information about popular services that might be relevant:\n{json.dumps(services, indent=2)}"

        # Define the system instructions as a preamble
        system_instructions = """
You are BillTracker AI Assistant that helps users manage their bills and finances.
You can provide information about bills, suggest alternatives, and analyze spending patterns.

For services like WiFi, streaming, etc., you can suggest popular options and their estimated costs based on the provided service data.

When the user wants to perform an action like adding a bill, removing a bill, or setting a reminder,
respond with a special action format:

ACTION: add_bill
DETAILS: {"bill_name": "NAME", "amount": AMOUNT, "due_date": "YYYY-MM-DD"}

ACTION: remove_bill
DETAILS: {"bill_name": "NAME"} 

ACTION: set_reminder
DETAILS: {"bill_name": "NAME", "reminder_date": "YYYY-MM-DD"}

For information queries, respond normally with helpful information. 
For service recommendations, include pricing, features, and alternatives.
"""

        # Simplified prompt format for the Gemini model
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            # Send as a single text prompt with all the context
            prompt = f"{system_instructions}\n\nUser query: {user_query}\n\nHere are the current bills:\n{bill_summary}{service_data}\n\nPlease provide a relevant response."
            
            response = model.generate_content(prompt)
            ai_response = response.text if response.text else "I'm sorry, I couldn't generate a response."
        except Exception as api_error:
            print(f"Gemini API error: {str(api_error)}")
            ai_response = f"Error calling AI service: {str(api_error)}"

        return jsonify({
            "response": ai_response, 
            "bills": bill_summary
        })
    except Exception as e:
        print(f"Error in AI query: {str(e)}")
        import traceback
        traceback.print_exc()  # Print full stack trace for debugging
        return jsonify({"response": f"Error: {str(e)}"}), 500

# Serve all HTML and static files
@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory(os.getcwd(), filename)
if __name__ == '__main__':
    app.run(debug=True)
