import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from tinydb import TinyDB, Query
from flask_mail import Mail, Message
import datetime
import google.generativeai as genai
import json
from dotenv import load_dotenv  # Add this import

# Load environment variables from .env file
load_dotenv()  # This loads the variables from .env

# Configure Gemini API with key from environment variables
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Warning: GEMINI_API_KEY not found in environment variables.")
genai.configure(api_key=api_key)

# Modify this line in your app.py file
import os
from tinydb import TinyDB

# Create a directory path that works with Render's free tier
if os.environ.get('RENDER'):
    # Use /tmp directory for Render (will be wiped on redeploy but works for free tier)
    os.makedirs('/tmp/billtracker', exist_ok=True)
    db_path = '/tmp/billtracker/bills.json'
else:
    # Local development path
    db_path = 'bills.json'

db = TinyDB(db_path)

app = Flask(__name__)

# Enable CORS - add your Netlify URL here when you get it
CORS(app, origins=["https://billweb.netlify.app/", "http://localhost:5000"])

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
    # For Render deployment, return a simple JSON response
    return jsonify({
        "status": "online",
        "message": "BillTracker API is running",
        "endpoints": [
            "/bills", 
            "/reminders", 
            "/insights",
            "/ai-query",
            "/ping"
        ]
    })

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
    
    # Use the Query object
    Bill = Query()
    
    # Check if it's a temporary ID (starts with 'temp-')
    if bill_id and bill_id.startswith('temp-'):
        # For temporary IDs, use string comparison
        db.remove(Bill.id == bill_id)
    else:
        try:
            # For regular numeric IDs, convert to integer
            numeric_id = int(bill_id)
            db.remove(Bill.id == numeric_id)
        except ValueError:
            # If conversion fails, try as string
            db.remove(Bill.id == bill_id)
            
    return jsonify({'message': 'Bill deleted successfully!'}), 200

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
    try:
        data = request.json
        email = data.get('email')
        bill_name = data.get('bill_name')
        due_date = data.get('due_date')
        amount = data.get('amount', 'N/A')
        
        if not email or not bill_name or not due_date:
            return jsonify({"error": "Missing required fields"}), 400
            
        msg = Message(
            subject=f"Bill Reminder: {bill_name} is due soon!",
            sender=os.environ.get('MAIL_USERNAME'),
            recipients=[email]
        )
        
        msg.body = f"""
        Hello,
        
        This is a reminder that your bill "{bill_name}" is due on {due_date}.
        Amount: ${amount}
        
        Please make sure to pay it on time to avoid late fees.
        
        Thank you,
        BillTracker App
        """
        
        mail.send(msg)
        return jsonify({"message": "Reminder email sent successfully"})
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Get reminders for upcoming due dates
@app.route('/reminders', methods=['GET'])
def get_reminders():
    try:
        today = datetime.date.today()
        upcoming_bills = []
        
        for bill in db.all():
            try:
                # Check if due_date exists
                if 'due_date' not in bill:
                    print(f"Warning: Bill '{bill.get('bill_name', 'Unnamed')}' has no due_date field")
                    continue
                
                # Handle different date formats
                due_date_str = bill['due_date']
                due_date = None
                
                # Try different date formats
                date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']
                for fmt in date_formats:
                    try:
                        due_date = datetime.datetime.strptime(due_date_str, fmt).date()
                        break
                    except ValueError:
                        continue
                
                # If no format worked, try to parse as ISO format
                if due_date is None:
                    try:
                        due_date = datetime.datetime.fromisoformat(due_date_str.replace('Z', '+00:00')).date()
                    except ValueError:
                        print(f"Warning: Could not parse due date '{due_date_str}' for bill '{bill.get('bill_name', 'Unnamed')}'")
                        continue
                
                # Add to upcoming bills if due date is today or in the future
                if due_date >= today:
                    upcoming_bills.append(bill)
                    
            except Exception as e:
                print(f"Error processing bill: {str(e)}")
                continue
                
        return jsonify(upcoming_bills)
    except Exception as e:
        print(f"Error in reminders endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

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

# Add this endpoint to get personalized free alternatives based on user's bills
@app.route('/free-alternatives', methods=['GET'])
def get_free_alternatives():
    try:
        # Get all bills from the database
        bills = db.all()
        
        # Filter for likely subscription services
        subscription_keywords = [
            'spotify', 'netflix', 'disney', 'hulu', 'hbo', 'prime', 'youtube', 'apple music',
            'office', 'microsoft', 'adobe', 'photoshop', 'dropbox', 'google one', 'icloud',
            'paramount', 'peacock', 'starz', 'showtime', 'crunchyroll', 'pandora', 'tidal'
        ]
        
        potential_subscriptions = []
        
        for bill in bills:
            bill_name = bill.get('bill_name', '').lower()
            # Check if bill name contains any subscription keywords
            if any(keyword in bill_name for keyword in subscription_keywords) or bill.get('category') == 'Subscriptions':
                potential_subscriptions.append({
                    'name': bill['bill_name'],
                    'amount': bill['amount']
                })
        
        # If no subscriptions found, return default alternatives
        if not potential_subscriptions:
            return jsonify({
                "message": "No subscription services detected in your bills",
                "alternatives": get_default_alternatives()
            })
        
        # Use Gemini to generate free alternatives for the found subscriptions
        alternatives = []
        
        for subscription in potential_subscriptions[:3]:  # Limit to top 3 to avoid too many API calls
            alt = get_alternative_for_subscription(subscription)
            if alt:
                alternatives.append(alt)
        
        # If we didn't get any valid alternatives, return defaults
        if not alternatives:
            alternatives = get_default_alternatives()
            
        return jsonify({
            "message": f"Found {len(potential_subscriptions)} subscription services in your bills",
            "alternatives": alternatives
        })
    except Exception as e:
        print(f"Error getting free alternatives: {str(e)}")
        return jsonify({
            "error": str(e),
            "alternatives": get_default_alternatives()
        }), 500

def get_alternative_for_subscription(subscription):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""
        The user is paying ${subscription['amount']} for {subscription['name']}.
        Suggest a completely free alternative to {subscription['name']}.
        Format your response in JSON strictly following this structure:
        {{
            "paid_service": "Original service name",
            "paid_amount": $amount_per_month,
            "free_alternative": "Name of free alternative",
            "savings": $yearly_savings,
            "logo_hint": "Icon name suggestion for the alternative (e.g., youtube, tv, film, play, file-word, etc.)",
            "free_logo_hint": "Icon name suggestion for the free service"
        }}
        ONLY return the JSON, no other text.
        """
        
        response = model.generate_content(prompt)
        response_text = response.text
        
        # Clean up response to ensure it's valid JSON
        response_text = response_text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parse the JSON response
        alternative = json.loads(response_text)
        return alternative
    except Exception as e:
        print(f"Error generating alternative for {subscription['name']}: {str(e)}")
        return None

def get_default_alternatives():
    return [
        {
            "paid_service": "Spotify Premium",
            "paid_amount": 9.99,
            "free_alternative": "YouTube Music",
            "savings": 120,
            "logo_hint": "spotify",
            "free_logo_hint": "youtube"
        },
        {
            "paid_service": "Netflix",
            "paid_amount": 15.49,
            "free_alternative": "Tubi TV",
            "savings": 186,
            "logo_hint": "film",
            "free_logo_hint": "tv"
        },
        {
            "paid_service": "Microsoft 365",
            "paid_amount": 6.99,
            "free_alternative": "LibreOffice",
            "savings": 84,
            "logo_hint": "file-word",
            "free_logo_hint": "file-alt"
        }
    ]

# Add endpoint to get average spending percentages from all users
@app.route('/average-spending', methods=['GET'])
def get_average_spending():
    try:
        # Get all bills from the database
        bills = db.all()
        
        if not bills:
            return jsonify({})
            
        # Calculate total amount spent
        total_spent = sum(bill.get('amount', 0) for bill in bills)
        
        if total_spent == 0:
            return jsonify({})
            
        # Group bills by category
        categories = {}
        for bill in bills:
            category = bill.get('category', 'Other')
            if category not in categories:
                categories[category] = 0
            categories[category] += bill.get('amount', 0)
        
        # Calculate percentage for each category
        category_percentages = {
            category: (amount / total_spent) * 100 
            for category, amount in categories.items()
        }
        
        return jsonify(category_percentages)
    except Exception as e:
        print(f"Error getting average spending: {str(e)}")
        return jsonify({}), 500

@app.route('/category-comparison', methods=['GET'])
def get_category_comparison():
    try:
        # Get all bills from the database
        all_bills = db.all()
        
        # Group by category and calculate total spending per category
        category_totals = {}
        total_spending = 0
        
        for bill in all_bills:
            category = bill.get('category', 'Other')
            amount = float(bill.get('amount', 0))
            
            if category not in category_totals:
                category_totals[category] = 0
            
            category_totals[category] += amount
            total_spending += amount
        
        # Calculate percentages
        category_percentages = {}
        
        for category, amount in category_totals.items():
            if total_spending > 0:
                category_percentages[category] = round((amount / total_spending) * 100, 1)
            else:
                category_percentages[category] = 0
        
        # Make sure all standard categories have values (even if zero)
        standard_categories = ["Utilities", "Entertainment", "Subscriptions", 
                              "Insurance", "Rent", "Transportation", "Food", "Other"]
        
        for category in standard_categories:
            if category not in category_percentages:
                category_percentages[category] = 0
                
        return jsonify(category_percentages)
    
    except Exception as e:
        print(f"Error getting category comparison: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Add a route to serve the JSON database file for backup
@app.route('/api/download-db', methods=['GET'])
def download_db():
    return send_from_directory(os.path.dirname(db_path), os.path.basename(db_path), as_attachment=True)

# Add a route to upload a database backup
@app.route('/api/upload-db', methods=['POST'])
def upload_db():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    try:
        file.save(db_path)
        return jsonify({"message": "Database restored successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "ok", "message": "App is running"}), 200

if __name__ == "__main__":
    # Use environment variable for port
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
