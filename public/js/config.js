/**
 * Configuration utility for BillTracker application
 */

// Define API base URL based on environment
function getApiBaseUrl() {
    // For production deployment
    if (window.location.hostname === 'billweb.netlify.app') {
        return 'https://billtracker-backend.onrender.com';
    }
    // For local development
    return 'http://localhost:5000';
}
