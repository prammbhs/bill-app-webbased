# Bill Reminder Web App

The **Bill Reminder Web App** is a free-to-use, web-based application designed to help users manage their bills effectively. It integrates with multiple service providers, provides AI-powered insights, and sends reminders to prevent late payments.

## Features

### Core Features
- **Bill Management**: Add, update, and delete bills with ease.
- **AI Assistant**: Ask billing-related questions and get insights powered by natural language processing.
- **Reminders**: Receive browser notifications and email reminders for upcoming bills.
- **Spending Analysis**: View spending trends and category breakdowns using interactive charts.
- **Cost-Saving Suggestions**: Get AI-driven recommendations for free alternatives to paid services.

### User Interface
- **Responsive Design**: Built with Bootstrap for seamless use across devices.
- **Navigation Sidebar**: Quick access to Dashboard, Add Bill, History, AI Assistant, and Settings.
- **Charts**: Visualize spending trends with Chart.js.

### Backend & API
- **REST API**: Add, update, fetch, and delete bills using Flask.
- **Local Storage**: TinyDB for lightweight, JSON-based storage.
- **AI Integration**: Natural language queries for bill-related insights.

## Technology Stack
-**Mern Stack**

### Frontend
- HTML, CSS, JavaScript
- Bootstrap for responsive design
- Chart.js for data visualization

### Backend
- Flask (Python) for API and server-side logic
- TinyDB for local JSON-based storage

### Notifications
- Browser Notification API
- Email reminders via Flask-Mail/SMTP

## Installation

### Prerequisites
- Python 3.7 or higher
- Node.js (optional, for frontend development)

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/bill-reminder-web-app.git
   cd bill-reminder-web-app
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the Flask server:
   ```bash
   python app.py
   ```
4. Open `index.html` in your browser to access the app.

## Usage

### Adding a Bill
1. Navigate to the **Add Bill** page.
2. Fill in the bill details (name, amount, due date, category, etc.).
3. Optionally, enable reminders and set notification preferences.
4. Click **Add Bill** to save.

### Viewing Bills
- Access the **Dashboard** to view upcoming bills and spending summaries.
- Use the **Bill History** page to filter and review past bills.

### AI Assistant
- Go to the **AI Assistant** page.
- Ask questions like:
  - "When is my next bill due?"
  - "How much do I spend on subscriptions?"
  - "Where can I save money?"

## Deployment

### Frontend
- Host on GitHub Pages or Netlify.

### Backend
- Deploy the Flask app on Render or a free-tier VPS.

## Future Enhancements
- Voice command support.
- Bill payment integrations.
- Multi-user support for families or businesses.

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request.

## Contact
For questions or support, please contact [paramjeetpatelmbhs@gmail.com].
