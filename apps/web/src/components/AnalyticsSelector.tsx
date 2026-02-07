// src/components/AnalyticsSelector.tsx
import React from 'react';

export function AnalyticsSelector({ queries, selected, onChange }) {
  return (
    <select value={selected} onChange={(e) => onChange(e.target.value)}>
      <option value="">Select an analytics…</option>
      {queries.map((q) => (
        <option key={q.id} value={q.id}>
          {q.name}
        </option>
      ))}
    </select>
  );
}
