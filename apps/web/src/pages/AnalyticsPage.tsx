// src/pages/AnalyticsPage.tsx
import React, { useEffect, useState } from "react";
import { AnalyticsSelector } from "../components/AnalyticsSelector";
import { fetchQueryList, runQuery } from "../utils/analytics";
import { chartRegistry } from "../utils/chartRegistry";

export default function AnalyticsPage() {
  const [queryList, setQueryList] = useState([]);
  const [selectedQuery, setSelectedQuery] = useState("");
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchQueryList().then(setQueryList);
  }, []);

  useEffect(() => {
    if (selectedQuery) {
      runQuery(selectedQuery).then(setData);
    }
  }, [selectedQuery]);

  const ChartComponent = selectedQuery ? chartRegistry[selectedQuery] : null;

  return (
    <div>
      <h1>Analytics Dashboard</h1>

      <AnalyticsSelector
        queries={queryList}
        selected={selectedQuery}
        onChange={setSelectedQuery}
      />

      <hr />

      {ChartComponent && data && (
        <ChartComponent data={data} />
      )}
    </div>
  );
}

