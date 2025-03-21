from tinydb import TinyDB
import datetime
import random
import uuid

# Initialize the database
db = TinyDB('bills.json')

# Clear existing bills if needed (comment this out if you want to keep existing bills)
db.truncate()

# Categories with emphasis on Subscriptions
categories = [
    "Subscriptions",  # This will be weighted more heavily
    "Entertainment",  # Many entertainment services are subscription-based
    "Utilities", 
    "Insurance", 
    "Rent", 
    "Transportation", 
    "Food", 
    "Other"
]

# Define weighted category selection (50% chance of subscriptions)
weighted_categories = ["Subscriptions"] * 10 + ["Entertainment"] * 5 + categories

# Expanded list of subscription apps and services
subscription_apps = [
    {"name": "Netflix", "typical_amount": 15.99},
    {"name": "Disney+", "typical_amount": 9.99},
    {"name": "Hulu", "typical_amount": 7.99},
    {"name": "Spotify Premium", "typical_amount": 9.99},
    {"name": "YouTube Premium", "typical_amount": 11.99},
    {"name": "Apple Music", "typical_amount": 9.99},
    {"name": "Amazon Prime", "typical_amount": 14.99},
    {"name": "HBO Max", "typical_amount": 14.99},
    {"name": "Paramount+", "typical_amount": 4.99},
    {"name": "Peacock Premium", "typical_amount": 4.99},
    {"name": "Adobe Creative Cloud", "typical_amount": 54.99},
    {"name": "Microsoft 365", "typical_amount": 6.99},
    {"name": "Google One Storage", "typical_amount": 1.99},
    {"name": "iCloud Storage", "typical_amount": 2.99},
    {"name": "Dropbox Plus", "typical_amount": 11.99},
    {"name": "LastPass Premium", "typical_amount": 3.99},
    {"name": "NordVPN", "typical_amount": 11.99},
    {"name": "ExpressVPN", "typical_amount": 12.99},
    {"name": "GitHub Pro", "typical_amount": 7.00},
    {"name": "Slack Pro", "typical_amount": 6.67},
    {"name": "Notion Pro", "typical_amount": 5.00},
    {"name": "Evernote Premium", "typical_amount": 7.99},
    {"name": "Headspace", "typical_amount": 12.99},
    {"name": "Calm", "typical_amount": 14.99},
    {"name": "NY Times Digital", "typical_amount": 17.00},
    {"name": "Wall Street Journal", "typical_amount": 19.99},
    {"name": "Medium", "typical_amount": 5.00},
    {"name": "Audible", "typical_amount": 14.95},
    {"name": "Canva Pro", "typical_amount": 12.99},
    {"name": "Grammarly Premium", "typical_amount": 11.66},
]

# Sample bill names for each category
bill_names = {
    "Utilities": [
        "Electricity Bill", 
        "Water Bill", 
        "Gas Bill", 
        "Internet Service", 
        "Mobile Phone", 
        "Landline Phone"
    ],
    "Entertainment": [
        "Netflix", 
        "Amazon Prime", 
        "Disney+", 
        "Spotify Premium", 
        "HBO Max", 
        "Movie Tickets",
        "Apple TV+",
        "Twitch Subscription"
    ],
    "Subscriptions": [app["name"] for app in subscription_apps],
    "Insurance": [
        "Health Insurance", 
        "Car Insurance", 
        "Home Insurance", 
        "Life Insurance", 
        "Travel Insurance", 
        "Renters Insurance"
    ],
    "Rent": [
        "Apartment Rent", 
        "Office Space Rent", 
        "Mortgage Payment", 
        "Vacation Rental", 
        "Storage Unit Rent", 
        "Garage Rent"
    ],
    "Transportation": [
        "Car Payment", 
        "Fuel", 
        "Public Transit Pass", 
        "Uber/Lyft", 
        "Car Maintenance", 
        "Parking Fee"
    ],
    "Food": [
        "Grocery Store", 
        "Restaurant Bill", 
        "Food Delivery Subscription", 
        "Coffee Shop", 
        "Meal Subscription", 
        "Cafeteria"
    ],
    "Other": [
        "Clothing", 
        "Home Repairs", 
        "Education Fees", 
        "Medical Bill", 
        "Pet Care", 
        "Charity Donation"
    ]
}

# Billing cycles for subscriptions
billing_cycles = ["Monthly", "Annual", "Quarterly"]
billing_cycle_weights = [70, 25, 5]  # Most subscriptions are monthly

# Payment methods with emphasis on digital payment methods
payment_methods = [
    "Credit Card", 
    "PayPal", 
    "Apple Pay", 
    "Google Pay", 
    "Bank Transfer", 
    "Venmo",
    "Cash App",
    "Automatic Bank Debit",
    "Cryptocurrency"
]

# Status options
statuses = ["paid", "pending", "overdue"]

# Current date
today = datetime.datetime.now().date()

# Generate 20 bills with varied data but emphasis on subscriptions
for i in range(1, 21):
    # Select random category with weighting toward subscriptions
    category = random.choice(weighted_categories)
    
    # Select random bill name from that category
    bill_name = random.choice(bill_names[category])
    
    # For subscriptions, use the typical amount if available
    if category == "Subscriptions":
        # Find the subscription in our detailed list
        subscription_details = next((app for app in subscription_apps if app["name"] == bill_name), None)
        
        if subscription_details:
            # Use the typical amount with some variation
            base_amount = subscription_details["typical_amount"]
            # Add up to 20% variation to simulate different tiers
            amount = round(base_amount * random.uniform(0.9, 1.2), 2)
        else:
            # Fallback for any new subscriptions not in the detailed list
            amount = round(random.uniform(4.99, 29.99), 2)
    else:
        # For non-subscriptions, use the original logic
        if category == "Rent":
            # Higher amounts for rent
            amount = round(random.uniform(500, 3000), 2)
        elif category == "Utilities":
            # Medium amounts for utilities
            amount = round(random.uniform(30, 300), 2)
        else:
            # Standard range for other categories
            amount = round(random.uniform(5, 200), 2)
    
    # Determine billing cycle for subscriptions
    if category == "Subscriptions" or category == "Entertainment":
        billing_cycle = random.choices(billing_cycles, weights=billing_cycle_weights)[0]
        
        # Adjust amount for non-monthly billing cycles
        if billing_cycle == "Annual":
            # Annual subscriptions often offer a discount (e.g., 10-20% off)
            monthly_equivalent = amount
            amount = round(monthly_equivalent * 12 * random.uniform(0.8, 0.9), 2)
            bill_name = f"{bill_name} (Annual)"
        elif billing_cycle == "Quarterly":
            monthly_equivalent = amount
            amount = round(monthly_equivalent * 3, 2)
            bill_name = f"{bill_name} (Quarterly)"
        else:
            bill_name = f"{bill_name} (Monthly)"
    else:
        billing_cycle = "Monthly"  # Default for non-subscription bills
    
    # Generate random due date - for subscriptions typically around the same day each month
    if category == "Subscriptions" or category == "Entertainment":
        # For subscriptions, set a recurring day of month (1-28)
        due_day = random.randint(1, 28)
        
        # Create a future due date with the chosen day
        next_month = today.replace(day=1) + datetime.timedelta(days=32)
        next_month = next_month.replace(day=min(due_day, 28))
        
        # Randomly decide if it's this month or next month
        if random.random() < 0.5 and today.day < due_day:
            # This month if today's day is less than the due day
            try:
                due_date = today.replace(day=due_day)
            except ValueError:
                # Handle months with fewer days
                due_date = today.replace(day=today.day)
        else:
            # Next month
            due_date = next_month
            
        # Some subscriptions might have already billed this cycle
        # So randomly set some to be paid already
        if random.random() < 0.4:
            paid = True
            status = "paid"
            # The payment likely happened a few days ago
            payment_date = due_date - datetime.timedelta(days=random.randint(1, 5))
        else:
            paid = False
            # If the due date is past, mark as overdue
            if due_date < today:
                status = "overdue"
            else:
                status = "pending"
            payment_date = None
    else:
        # For non-subscriptions, use the original logic
        days_offset = random.randint(-30, 60)
        due_date = today + datetime.timedelta(days=days_offset)
        
        # Determine status based on due date
        if due_date < today:
            # Past due date - either paid or overdue
            status = random.choice(["paid", "overdue"])
            paid = status == "paid"
        else:
            # Future due date - either paid or pending
            status = random.choice(["paid", "pending"])
            paid = status == "paid"
        
        # If paid, payment was likely before or on the due date
        if paid:
            payment_days_offset = random.randint(-10, 0)
            payment_date = due_date + datetime.timedelta(days=payment_days_offset)
        else:
            payment_date = None
    
    # Convert dates to string format
    due_date_str = due_date.strftime('%Y-%m-%d')
    
    # Generate descriptive notes
    if category == "Subscriptions" or category == "Entertainment":
        notes_options = [
            f"{billing_cycle} subscription to {bill_name.split('(')[0].strip()}",
            f"Auto-renews {billing_cycle.lower()}",
            f"Subscription started on {(due_date - datetime.timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d')}",
            f"Increased from ${round(amount * 0.9, 2)} last {billing_cycle.lower()}",
            f"Free trial ends on {(today + datetime.timedelta(days=random.randint(5, 30))).strftime('%Y-%m-%d')}",
            f"New premium tier",
            f"Shared account with family",
            ""  # Empty notes option
        ]
    else:
        notes_options = [
            f"Monthly {bill_name.split()[0].lower()} bill",
            f"Automatic payment scheduled",
            f"Increased from last month",
            f"Special discount applied",
            f"New service provider",
            f"Payment due on the {due_date.day}th",
            ""  # Empty notes option
        ]
    
    notes = random.choice(notes_options)
    
    # Create a unique ID
    bill_id = i
    
    # Setup payment history for paid bills
    payments = []
    if paid and payment_date:
        # For subscriptions, usually just one payment
        if category == "Subscriptions" or category == "Entertainment":
            payments.append({
                "amount": amount,
                "date": payment_date.strftime('%Y-%m-%d'),
                "method": random.choice(payment_methods)
            })
        else:
            # For other bills, might have split payments
            has_split_payment = random.random() < 0.3  # 30% chance
            
            if has_split_payment:
                # Generate 2-3 payment entries
                num_payments = random.randint(2, 3)
                payment_total = 0
                
                for j in range(num_payments):
                    payment_amount = round(amount / num_payments, 2)
                    payment_total += payment_amount
                    
                    # Last payment covers any remaining amount to ensure total matches
                    if j == num_payments - 1:
                        payment_amount = round(amount - payment_total + payment_amount, 2)
                    
                    # Payment dates spread out
                    payment_days_offset = -1 * (j + 1) * random.randint(3, 7)
                    payment_date_j = payment_date + datetime.timedelta(days=payment_days_offset)
                    
                    payments.append({
                        "amount": payment_amount,
                        "date": payment_date_j.strftime('%Y-%m-%d'),
                        "method": random.choice(payment_methods)
                    })
            else:
                # Single payment
                payments.append({
                    "amount": amount,
                    "date": payment_date.strftime('%Y-%m-%d'),
                    "method": random.choice(payment_methods)
                })
    
    # Create bill object
    bill = {
        "id": bill_id,
        "bill_name": bill_name,
        "amount": amount,
        "due_date": due_date_str,
        "category": category,
        "paid": paid,
        "notes": notes,
        "status": status,
        "billing_cycle": billing_cycle
    }
    
    # Add payments if they exist
    if payments:
        bill["payments"] = payments
    
    # Add recurring flag for subscriptions
    if category == "Subscriptions" or category == "Entertainment":
        bill["recurring"] = True
    else:
        bill["recurring"] = random.random() < 0.3  # 30% of other bills are recurring
    
    # Add to the database
    db.insert(bill)

print(f"Successfully generated 20 test bills in bills.json with emphasis on subscription apps")

# Print a summary of the generated bills
bills = db.all()
print(f"\nSummary of generated bills:")
print(f"Total bills: {len(bills)}")

category_counts = {}
status_counts = {"paid": 0, "pending": 0, "overdue": 0}
subscription_count = 0
recurring_count = 0

for bill in bills:
    category = bill.get('category')
    category_counts[category] = category_counts.get(category, 0) + 1
    
    status = bill.get('status')
    status_counts[status] = status_counts.get(status, 0) + 1
    
    if bill.get('recurring', False):
        recurring_count += 1
        
    if category == "Subscriptions" or "(" in bill.get('bill_name', ''):
        subscription_count += 1

print("\nBills by category:")
for category, count in category_counts.items():
    print(f"- {category}: {count}")

print("\nBills by status:")
for status, count in status_counts.items():
    print(f"- {status.capitalize()}: {count}")

print(f"\nSubscription bills: {subscription_count}")
print(f"Recurring bills: {recurring_count}")

print("\nSubscription app examples:")
subscription_examples = [bill for bill in bills if bill.get('category') == 'Subscriptions'][:5]
for example in subscription_examples:
    print(f"- {example['bill_name']} (${example['amount']:.2f}, {example['status']})")