import React from 'react';
import './App.css';  // Assuming you're using a CSS file for styles
import AnalyticsPage from './pages/AnalyticsPage';  // Import the AnalyticsPage component
import AnalyticsDashboard from './pages/Dashboard';

function App() {
  return (
    <div className="App">
      <h1>Welcome to the Analytics App</h1>
      {/* Render the AnalyticsPage component */}
      <AnalyticsPage />
    </div>
  );
}

export default App;
