import React from "react";
import { BrowserRouter as Router, Routes, Route, useParams } from "react-router-dom";
import AnalyticsDashboard from "./pages/Dashboard";

const AnalyticsDashboardWrapper: React.FC = () => {
  const { tenantId, eventDate } = useParams<{
    tenantId: string;
    eventDate: string;
  }>();

  if (!tenantId || !eventDate) {
    return <div>Missing parameters</div>;
  }

  return (
    <AnalyticsDashboard
      tenantId={tenantId}
      eventDate={eventDate}
    />
  );
};

const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route
          path="/v2/analytics/:tenantId/:eventDate"
          element={<AnalyticsDashboardWrapper />}
        />
      </Routes>
    </Router>
  );
};

export default App;
