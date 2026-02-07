import React, { useState, useEffect } from 'react';
import { fetchQueryList, runQuery } from '../utils/analytics';  // Assuming these are your API functions
import Chart from './Chart'; // Import the Chart component

const AnalyticsPage: React.FC = () => {
  const [queryList, setQueryList] = useState<string[]>([]); // To store the list of queries
  const [loading, setLoading] = useState<boolean>(true); // Loading state
  const [selectedQuery, setSelectedQuery] = useState<string>(''); // Selected query ID
  const [queryResult, setQueryResult] = useState<any>(null); // Store query results

  // Fetch available queries when component mounts
  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await fetchQueryList();
        setQueryList(data); // Set the list of available queries
      } catch (err) {
        console.error('Error fetching query list', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Handle running the query and fetching results
  const handleRunQuery = async () => {
    if (!selectedQuery) {
      alert('Please select a query first.');
      return;
    }
    setLoading(true);
    try {
      const rawResult = await runQuery(selectedQuery);

      // Ensure rawResult contains data
      if (!rawResult || rawResult.length === 0) {
        alert('No data found for this query');
        return;
      }

      let labels = [];
      let values = [];

      // Data mapping for each query type
      switch (selectedQuery) {
        case 'avg_entropy': {
          labels = rawResult.map((item: any) => item.qname);
          values = rawResult.map((item: any) => item.avg_entropy); // or item.query_count
          break;
        }
        case 'nx_domain': {
          labels = rawResult.map((item: any) => item.qname);
          values = rawResult.map((item: any) => item.nxdomain_count);
          break;
        }
        case 'qname_length': {
          labels = rawResult.map((item: any) => item.qname);
          values = rawResult.map((item: any) => item.qname_length);
          break;
        }
        case 'top_domains': {
          labels = rawResult.map((item: any) => item.qname);
          values = rawResult.map((item: any) => item.query_count);
          break;
        }
        case 'top_query_types': {
          labels = rawResult.map((item: any) => item.qtype);
          values = rawResult.map((item: any) => item.query_count);
          break;
        }
        case 'topn_clients': {
          labels = rawResult.map((item: any) => item.client_ip);
          values = rawResult.map((item: any) => item.query_count);
          break;
        }
        default:
          alert('Unknown query type');
          return;
      }

      const formattedResult = {
        labels,
        values,
      };

      setQueryResult(formattedResult); // Set the result for the chart
    } catch (err) {
      console.error('Error running query', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>Analytics</h1>

      {loading && <p>Loading available queries...</p>}

      {/* Query Selection */}
      <div>
        <label htmlFor="querySelect">Select Query:</label>
        <select
          id="querySelect"
          value={selectedQuery}
          onChange={(e) => setSelectedQuery(e.target.value)}
          disabled={loading}
        >
          <option value="">-- Select a Query --</option>
          {queryList.map((queryId) => (
            <option key={queryId} value={queryId}>
              {queryId}
            </option>
          ))}
        </select>
      </div>

      {/* Run Query Button */}
      <div>
        <button onClick={handleRunQuery} disabled={loading || !selectedQuery}>
          Run Query
        </button>
      </div>

      {/* Render Chart if data is available */}
      {queryResult && <Chart queryId={selectedQuery} data={queryResult} />}
    </div>
  );
};

export default AnalyticsPage;
