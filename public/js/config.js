// Configuration variables for the application
const config = {
    // API base URL - dynamically set based on environment
    apiBaseUrl: function() {
        // Use production URL in production, localhost in development
        return window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
            ? 'http://localhost:5000'
            : 'https://billtracker-backend.onrender.com';  // Update with your actual Render URL
    }
};

// Helper function to get API base URL
function getApiBaseUrl() {
    return config.apiBaseUrl();
}