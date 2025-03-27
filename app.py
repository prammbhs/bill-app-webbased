import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from tinydb import TinyDB, Query
from flask_mail import Mail, Message
import datetime
import google.generativeai as genai
import json
from dotenv import load_dotenv  # Add this import
import random

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

# Create a function to generate sample data
def generate_sample_data():
    """Generate sample bills if database is empty"""
    if len(db.all()) == 0:
        print("Database is empty, generating sample data...")
        
        # Categories for bills
        categories = ["Utilities", "Entertainment", "Subscriptions", 
                     "Insurance", "Rent", "Transportation", "Food", "Other"]
        
        # Sample bill names for each category
        bill_names = {
            "Utilities": ["Electricity Bill", "Water Bill", "Gas Bill", "Internet Service"],
            "Entertainment": ["Netflix", "Disney+", "HBO Max", "Movie Tickets"],
            "Subscriptions": ["Spotify Premium", "Adobe Creative Cloud", "Microsoft 365", "Amazon Prime"],
            "Insurance": ["Health Insurance", "Car Insurance", "Renters Insurance", "Life Insurance"],
            "Rent": ["Apartment Rent", "Storage Unit", "Parking Space"],
            "Transportation": ["Car Payment", "Bus Pass", "Uber/Lyft", "Fuel"],
            "Food": ["Grocery Store", "DoorDash", "Hello Fresh", "Restaurant Bills"],
            "Other": ["Gym Membership", "Phone Bill", "Student Loans", "Credit Card"]
        }
        
        # Current date
        today = datetime.date.today()
        
        # Generate 15 random bills
        for i in range(1, 16):
            # Choose random category
            category = random.choice(categories)
            
            # Choose random bill name from that category
            bill_name = random.choice(bill_names[category])
            
            # Determine amount based on category
            if category == "Rent":
                amount = round(random.uniform(800, 2500), 2)
            elif category == "Insurance":
                amount = round(random.uniform(80, 300), 2)
            elif category == "Subscriptions":
                amount = round(random.uniform(5, 30), 2)
            else:
                amount = round(random.uniform(15, 200), 2)
                
            # Generate due date within next 30 days
            days_offset = random.randint(1, 30)
            due_date = today + datetime.timedelta(days=days_offset)
            due_date_str = due_date.strftime('%Y-%m-%d')
            
            # 30% chance the bill is already paid
            paid = random.random() < 0.3
            
            # Create bill object
            bill = {
                "id": i,
                "bill_name": bill_name,
                "amount": amount,
                "due_date": due_date_str,
                "category": category,
                "paid": paid,
                "status": "paid" if paid else "pending",
                "notes": f"Sample {category.lower()} bill",
                "recurring": category in ["Subscriptions", "Utilities", "Rent", "Insurance"]
            }
            
            # Add to database
            db.insert(bill)
            
        print(f"Generated {len(db.all())} sample bills")

# Create the Flask app
app = Flask(__name__)

# Enable CORS for all routes - this is the simplest approach for now
CORS(app, origins=["https://billweb.netlify.app"])

# Let's also add a proper CORS preflight handler
@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    response = app.make_default_options_response()
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

# Add this function to manually set CORS headers for all responses
@app.after_request
def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Configure Flask-Mail with credentials from environment variables
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
mail = Mail(app)

# Call function once after database is initialized but before routes are defined
generate_sample_data()

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
        
        # Check if this is a utility-related query
        utility_keywords = [
            'wifi', 'internet', 'broadband', 'electricity', 'power', 'water', 'gas', 'phone', 
            'utility', 'utilities', 'bill', 'bills', 'payment', 'service', 'subscription',
            'cable', 'tv', 'streaming', 'energy', 'provider', 'plan', 'discount',
            'connection', 'mobile', 'cell', 'landline', 'trash', 'garbage', 'sewage',
            'heat', 'heating', 'cool', 'cooling', 'compare', 'rate', 'price',
            'expensive', 'cheap', 'save', 'money', 'cost', 'recommendation'
        ]
        
        # More precise check for utility-related query
        is_utility_query = any(keyword in user_query.lower() for keyword in utility_keywords)
        
        # Add service data if this is a recommendation query
        service_data = ""
        if is_utility_query:
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

        # Define the system instructions as a preamble with strict topic restrictions
        system_instructions = """
You are BillTracker AI Assistant that ONLY helps users manage their bills, utilities, and household finances.

IMPORTANT RESTRICTION: You MUST ONLY respond to queries about household utilities, bills, services, 
and daily expenses like:
- Internet/WiFi services and providers
- Electricity, water, gas bills
- Phone plans and services
- Streaming services
- Insurance payments
- Rent or mortgage
- Subscriptions and recurring payments
- Tips to reduce utility bills
- Comparing service providers
- Bill payment options

For ANY query NOT related to these topics, respond ONLY with:
"I'm specifically designed to help with bill tracking and utility management. For questions about [topic], 
please consult a relevant resource or expert. Is there anything about your bills or household utilities 
I can assist with instead?"

Never provide recommendations, advice, or information on topics unrelated to household bills and utilities,
even if the user insists.

When the user wants to perform an action like adding a bill, removing a bill, or setting a reminder,
respond with a special action format:

ACTION: add_bill
DETAILS: {"bill_name": "NAME", "amount": AMOUNT, "due_date": "YYYY-MM-DD"}

ACTION: remove_bill
DETAILS: {"bill_name": "NAME"} 

ACTION: set_reminder
DETAILS: {"bill_name": "NAME", "reminder_date": "YYYY-MM-DD"}
"""

        # Add conversation history to the prompt
        conversation_context = f"\n\nConversation history:\n{conversation_history}\n" if conversation_history else ""

        # Force non-utility topics to get the restricted response
        if not is_utility_query:
            # Extract the likely topic from the query
            topic_words = user_query.lower().split()
            # Remove common words
            common_words = ['suggest', 'me', 'a', 'the', 'for', 'about', 'how', 'to', 'what', 'is', 'are', 'do', 'can', 'i', 'you']
            topic = ' '.join([word for word in topic_words if word not in common_words])
            
            restricted_response = f"I'm specifically designed to help with bill tracking and utility management. For questions about {topic}, please consult a relevant resource or expert. Is there anything about your bills or household utilities I can assist with instead?"
            return jsonify({"response": restricted_response})
        
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
@app.route('/free-alternatives', methods=['GET', 'OPTIONS'])
def get_free_alternatives():
    """
    Return suggestions for free alternatives to paid services
    """
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
        
    try:
        # In a real implementation, you would analyze the user's bills
        # and suggest relevant free alternatives based on their subscriptions
        
        alternatives = [
            {
                "paid_service": "Netflix",
                "paid_amount": 15.49,
                "free_alternative": "Tubi TV",
                "savings": 186,
                "logo_hint": "film",
                "free_logo_hint": "tv"
            },
            {
                "paid_service": "Spotify Premium",
                "paid_amount": 9.99,
                "free_alternative": "YouTube Music",
                "savings": 120,
                "logo_hint": "spotify",
                "free_logo_hint": "youtube"
            },
            {
                "paid_service": "Microsoft 365",
                "paid_amount": 6.99,
                "free_alternative": "LibreOffice",
                "savings": 84,
                "logo_hint": "file-word",
                "free_logo_hint": "file-alt"
            },
            {
                "paid_service": "Disney+",
                "paid_amount": 7.99,
                "free_alternative": "Pluto TV",
                "savings": 96,
                "logo_hint": "discord",
                "free_logo_hint": "play"
            }
        ]
        
        return jsonify({"alternatives": alternatives})
        
    except Exception as e:
        print(f"Error getting free alternatives: {str(e)}")
        return jsonify({"error": str(e)}), 500

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

@app.route('/category-comparison', methods=['GET', 'OPTIONS'])
def get_category_comparison():
    """
    Return average spending percentages by category for comparison
    """
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
        
    try:
        # Get user's actual percentages (could be used in the future)
        all_bills = db.all()
        
        # For now, we'll use simulated averages instead of real user data
        # In a production environment, this would be based on aggregate anonymous data
        avg_percentages = {
            'Utilities': 18.5,
            'Entertainment': 7.2,
            'Subscriptions': 6.8,
            'Insurance': 14.3,
            'Rent': 35.6,
            'Transportation': 8.9,
            'Food': 7.1,
            'Other': 1.6
        }
        
        return jsonify(avg_percentages)
        
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

# Import additional libraries for image processing
from PIL import Image
import base64
import io
import re
from datetime import datetime, timedelta
import random

@app.route('/extract-bill-data', methods=['POST', 'OPTIONS'])
def extract_bill_data():
    """
    Extract data from bill images using OCR and AI processing
    """
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
        
    try:
        data = request.json
        if not data or 'image' not in data:
            return jsonify({"error": "No image provided"}), 400
            
        # Get image data from base64 string
        image_data = data['image']
        # Remove the data:image/jpeg;base64, prefix if present
        if ',' in image_data:
            image_data = image_data.split(',')[1]
            
        # Decode base64 image
        decoded_image = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(decoded_image))
        
        # For demonstration purposes: Use mock data instead of actual OCR
        # In a production environment, you would use:
        # - Google Cloud Vision API
        # - Azure Computer Vision
        # - Amazon Textract
        # - Tesseract OCR 
        # - Or another OCR/AI service
        
        extracted_data = extract_bill_info_mock(image)
        
        return jsonify(extracted_data)
        
    except Exception as e:
        print(f"Error extracting bill data: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

def extract_bill_info_mock(image):
    """
    Mock function to simulate extracting bill information
    In a real implementation, this would use OCR and NLP
    """
    # Generate mock bill types
    bill_types = [
        {"bill_name": "Electric Company", "amount": 89.75, "category": "Utilities"},
        {"bill_name": "Water Services", "amount": 45.50, "category": "Utilities"},
        {"bill_name": "Internet Provider", "amount": 59.99, "category": "Utilities"},
        {"bill_name": "Netflix", "amount": 15.99, "category": "Entertainment"},
        {"bill_name": "Rent", "amount": 1250.00, "category": "Rent"},
        {"bill_name": "Car Insurance", "amount": 112.50, "category": "Insurance"},
        {"bill_name": "Phone Bill", "amount": 75.00, "category": "Utilities"},
        {"bill_name": "Gym Membership", "amount": 39.99, "category": "Subscriptions"}
    ]
    
    # Pick a random bill type
    bill_info = random.choice(bill_types)
    
    # Generate a due date in the near future (1-30 days from now)
    days_ahead = random.randint(1, 30)
    due_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
    
    # Add due date to bill info
    bill_info["due_date"] = due_date
    
    # Add confidence scores (simulating AI confidence in the extraction)
    bill_info["name_confidence"] = random.uniform(0.75, 0.98)
    bill_info["amount_confidence"] = random.uniform(0.80, 0.95)
    bill_info["date_confidence"] = random.uniform(0.70, 0.90)
    
    return bill_info

if __name__ == "__main__":
    # Use environment variable for port
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
