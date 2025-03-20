document.addEventListener('DOMContentLoaded', function() {
    // Form submission handler
    document.getElementById('billForm').addEventListener('submit', function(event) {
        event.preventDefault();
        const billName = document.getElementById('billName').value;
        const amount = document.getElementById('amount').value;
        const dueDate = document.getElementById('dueDate').value;

        fetch('/bills', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ bill_name: billName, amount: parseFloat(amount), due_date: dueDate })
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            loadBills();
            updateTotalBillSummary();
        });
    });

    // Load bills function
    function loadBills() {
        fetch('/bills')
            .then(response => response.json())
            .then(data => {
                const billsList = document.getElementById('billsList');
                billsList.innerHTML = '';
                data.forEach(bill => {
                    const li = document.createElement('li');
                    li.className = 'list-group-item';
                    li.textContent = `${bill.bill_name} - $${bill.amount} (Due: ${bill.due_date})`;
                    billsList.appendChild(li);
                });
            });
    }

    // Update total bill summary
    function updateTotalBillSummary() {
        fetch('/bills')
            .then(response => response.json())
            .then(data => {
                const total = data.reduce((sum, bill) => sum + bill.amount, 0);
                document.getElementById('totalBillSummary').textContent = `Total Outstanding Bills: $${total.toFixed(2)}`;
            });
    }

    // Navigation event listeners
    document.getElementById('dashboardLink').addEventListener('click', function() {
        showSection('dashboard');
        loadBills();
        updateTotalBillSummary();
    });

    document.getElementById('addBillLink').addEventListener('click', function() {
        showSection('addBill');
    });

    document.getElementById('billHistoryLink').addEventListener('click', function() {
        showSection('billHistory');
        loadBills();
    });

    document.getElementById('aiQueryLink').addEventListener('click', function() {
        showSection('aiQuery');
    });

    document.getElementById('remindersLink').addEventListener('click', function() {
        showSection('reminders');
        loadReminders();
    });

    document.getElementById('insightsLink').addEventListener('click', function() {
        showSection('insights');
        loadInsights();
    });

    // Helper function to show only the selected section
    function showSection(sectionId) {
        const sections = ['dashboard', 'addBill', 'billHistory', 'aiQuery', 'reminders', 'insights'];
        sections.forEach(section => {
            document.getElementById(section).style.display = section === sectionId ? 'block' : 'none';
        });
    }

    // Chat message functions
    function addMessage(message, isUser = false) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
        
        if (isUser) {
            messageDiv.textContent = message;
        } else {
            // For bot messages, we'll handle more complex content
            const responseContainer = document.createElement('div');
            responseContainer.className = 'bot-response-container';
            
            // Simple text part
            const textPart = document.createElement('div');
            textPart.textContent = message.text || message;
            responseContainer.appendChild(textPart);
            
            // If we have bills data, add a table
            if (message.bills && message.bills.length > 0) {
                const table = document.createElement('table');
                table.className = 'bot-response-table';
                
                // Create header row
                const thead = document.createElement('thead');
                const headerRow = document.createElement('tr');
                headerRow.innerHTML = `
                    <th>Bill</th>
                    <th>Amount</th>
                    <th>Due Date</th>
                `;
                thead.appendChild(headerRow);
                table.appendChild(thead);
                
                // Create table body
                const tbody = document.createElement('tbody');
                message.bills.forEach(bill => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${bill.name}</td>
                        <td>$${bill.amount.toFixed(2)}</td>
                        <td>${bill.due_date}</td>
                    `;
                    tbody.appendChild(row);
                });
                
                table.appendChild(tbody);
                responseContainer.appendChild(table);
            }
            
            messageDiv.appendChild(responseContainer);
        }
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function showTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        typingIndicator.style.display = 'block';
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function hideTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        typingIndicator.style.display = 'none';
    }

    // AI input event handlers
    document.getElementById('aiInput').addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            document.getElementById('aiSubmit').click();
        }
    });

    document.getElementById('aiSubmit').addEventListener('click', function() {
        const query = document.getElementById('aiInput').value;
        if (query.trim() === "") {
            return;
        }

        // Add user message to chat
        addMessage(query, true);
        
        // Clear input
        document.getElementById('aiInput').value = '';
        
        // Show typing indicator
        showTypingIndicator();

        fetch('/ai-query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query })
        })
        .then(response => response.json())
        .then(data => {
            // Hide typing indicator
            hideTypingIndicator();
            
            // Format the bot response
            const botResponse = {
                text: data.response,
                bills: data.bills
            };
            
            // Add bot message to chat
            addMessage(botResponse);
        })
        .catch(error => {
            console.error('Error:', error);
            hideTypingIndicator();
            addMessage("I'm sorry, I couldn't process your request at the moment. Please try again later.");
        });
    });

    // Load reminders
    function loadReminders() {
        fetch('/reminders')
            .then(response => response.json())
            .then(data => {
                const remindersList = document.getElementById('remindersList');
                remindersList.innerHTML = '';
                data.forEach(bill => {
                    const li = document.createElement('li');
                    li.className = 'list-group-item';
                    li.textContent = `${bill.bill_name} - Due on ${bill.due_date}`;
                    remindersList.appendChild(li);
                });
            });
    }

    // Load insights
    function loadInsights() {
        fetch('/insights')
            .then(response => response.json())
            .then(data => {
                const insightsData = document.getElementById('insightsData');
                insightsData.innerHTML = `
                    Total Spent: $${data.total_spent.toFixed(2)}<br>
                    Frequent Services: ${data.frequent_services.join(', ')}<br>
                    Suggestions: ${data.suggestions}
                `;
            });
    }

    // Add a sample message after loading the page
    setTimeout(function() {
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages.children.length <= 1) {
            addMessage({
                text: "I can help answer questions about your bills. Try asking things like 'Which bill is due next?' or 'How much am I spending on subscriptions?'",
                bills: []
            });
        }
    }, 1000);

    // Initialize the page
    loadBills();
    updateTotalBillSummary();
});