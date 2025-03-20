Project Requirements

1. Overview

The Bill Reminder Web App is a free-to-use, web-based application designed to help users manage their bills effectively. It fetches billing details from multiple service providers, provides smart insights, and sends reminders to prevent late payments.

2. Technology Stack

Frontend: HTML, CSS, JavaScript, Bootstrap

Backend: Flask (Python)

Database: TinyDB (local JSON-based storage)

Charting: Chart.js (for data visualization)

Notifications: Browser Notification API + Email reminders (via Flask-Mail/SMTP)

3. Features

Core Features

Fetch and store bill details

View summary of total bill amount and due dates

Get AI-powered insights about bills

Receive reminders via browser notifications

Free Alternative Suggestions: AI-driven recommendations for free alternatives to paid services

User Interface (UI)

Responsive dashboard with Bootstrap

Sidebar for navigation (Dashboard, Add Bill, History, AI Query, Settings)

Charts to display spending trends

Backend & API

REST API using Flask

Endpoints for adding, updating, fetching, and deleting bills

AI integration for natural language queries

Reminder system for notifying users

Alternative Service Finder: API or database-driven feature to suggest free services

Data Handling

TinyDB for local storage of bill records

API requests to fetch bills from external providers

Deployment (Free Services)

Frontend: Hosted on GitHub Pages / Netlify

Backend: Flask app hosted on Render / Free-tier VPS

Database: TinyDB (local, no external hosting required)