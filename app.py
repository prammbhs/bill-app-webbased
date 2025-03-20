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

# Add this endpoint to delete bill by name
@app.route('/bills/by-name', methods=['DELETE'])
def delete_bill_by_name():
    data = request.json
    bill_name = data.get('bill_name')
    if not bill_name:
        return jsonify({"error": "No bill name provided"}), 400
        
    Bill = Query()
    removed = db.remove(Bill.bill_name == bill_name)
    if removed:
        return jsonify({"message": f"Bill '{bill_name}' deleted successfully!"})
    else:
        return jsonify({"message": "Bill not found"}), 404

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

# Enhanced insights endpoint that uses categories
@app.route('/insights', methods=['GET'])
def get_insights():
    bills = db.all()
    total_spent = sum(bill['amount'] for bill in bills)
    
    # Group bills by category
    categories = {}
    for bill in bills:
        category = bill.get('category', 'Other')
        if category not in categories:
            categories[category] = 0
        categories[category] += bill['amount']
    
    # Calculate percentage for each category
    category_percentages = {
        category: (amount / total_spent) * 100 
        for category, amount in categories.items()
    }
    
    # Find the highest spending category
    highest_category = max(categories.items(), key=lambda x: x[1], default=('None', 0))
    
    # Gemini API Call for saving suggestions based on highest category
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    The user spends the most on {highest_category[0]} category (${highest_category[1]:.2f}).
    Suggest 3 practical ways to save money on {highest_category[0]} expenses.
    Keep each suggestion brief (one sentence) and practical.
    Format as a bullet point list with 3 items.
    """
    
    response = model.generate_content(prompt)
    saving_suggestions = response.text if response.text else "No suggestions available."

    return jsonify({
        "total_spent": total_spent,
        "category_breakdown": categories,
        "category_percentages": category_percentages,
        "highest_spending_category": {
            "name": highest_category[0],
            "amount": highest_category[1]
        },
        "saving_suggestions": saving_suggestions
    })

# Modified AI query endpoint to better handle service recommendations
@app.route('/ai-query', methods=['POST', 'OPTIONS'])
def ai_query():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.json
        user_query = data.get('query')
        conversation_history = data.get('conversation_history', '')
        
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
You have a memory of the conversation so far, so you can refer to previous messages.
Maintain context: If the user previously mentioned wanting to delete a bill and then mentions a bill name, understand they want to delete that specific bill.

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

        # Add conversation history to the prompt
        conversation_context = f"\n\nConversation history:\n{conversation_history}\n" if conversation_history else ""

        # Simplified prompt format for the Gemini model
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            # Send as a single text prompt with all the context
            prompt = f"{system_instructions}\n\n{conversation_context}User query: {user_query}\n\nHere are the current bills:\n{bill_summary}{service_data}\n\nPlease provide a relevant response."
            
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

# Add this to your app.py file
@app.route('/classify-bill', methods=['POST'])
def classify_bill():
    try:
        data = request.json
        bill_name = data.get('bill_name')
        
        if not bill_name:
            return jsonify({"error": "No bill name provided"}), 400
            
        # Call Gemini API to classify the bill
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = f"""
        You are a bill categorization assistant. 
        Based on the bill name "{bill_name}", classify it into one of these categories:
        - Utilities (e.g., electricity, water, gas, phone, internet)
        - Entertainment (e.g., movie tickets, concerts, streaming services for media)
        - Subscriptions (e.g., recurring software payments, magazines, non-entertainment subscriptions)
        - Insurance (e.g., health, car, home insurance)
        - Rent (e.g., housing payments, rent, mortgage)
        - Transportation (e.g., fuel, car payments, public transit)
        - Food (e.g., groceries, restaurants, meal services)
        - Other (for anything that doesn't fit above)
        
        Return only the category name without any explanation.
        """
        
        response = model.generate_content(prompt)
        category = response.text.strip() if response.text else "Other"
        
        # Ensure the category matches one of our predefined categories
        valid_categories = ["Utilities", "Entertainment", "Subscriptions", 
                           "Insurance", "Rent", "Transportation", "Food", "Other"]
        
        if category not in valid_categories:
            # If Gemini returns something outside our categories, default to "Other"
            category = "Other"
            
        return jsonify({
            "category": category,
            "bill_name": bill_name
        })
    except Exception as e:
        print(f"Error in bill classification: {str(e)}")
        return jsonify({"error": str(e), "category": "Other"}), 500

# Add this to app.py - use this once to categorize all existing bills
@app.route('/admin/categorize-all-bills', methods=['GET'])
def categorize_all_bills():
    try:
        bills = db.all()
        categorized_count = 0
        
        for bill in bills:
            # Skip bills that already have a category
            if 'category' in bill and bill['category']:
                continue
                
            # Call Gemini API to classify the bill
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            prompt = f"""
            You are a bill categorization assistant. 
            Based on the bill name "{bill['bill_name']}", classify it into one of these categories:
            - Utilities (e.g., electricity, water, gas, phone, internet)
            - Entertainment (e.g., movie tickets, concerts, streaming services for media)
            - Subscriptions (e.g., recurring software payments, magazines, non-entertainment subscriptions)
            - Insurance (e.g., health, car, home insurance)
            - Rent (e.g., housing payments, rent, mortgage)
            - Transportation (e.g., fuel, car payments, public transit)
            - Food (e.g., groceries, restaurants, meal services)
            - Other (for anything that doesn't fit above)
            
            Return only the category name without any explanation.
            """
            
            response = model.generate_content(prompt)
            category = response.text.strip() if response.text else "Other"
            
            # Ensure the category matches one of our predefined categories
            valid_categories = ["Utilities", "Entertainment", "Subscriptions", 
                               "Insurance", "Rent", "Transportation", "Food", "Other"]
            
            if category not in valid_categories:
                category = "Other"
                
            # Update the bill with the category
            db.update({'category': category}, doc_ids=[bill.doc_id])
            categorized_count += 1
            
        return jsonify({
            "message": f"Successfully categorized {categorized_count} bills",
            "bills": db.all()
        })
    except Exception as e:
        print(f"Error categorizing bills: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
