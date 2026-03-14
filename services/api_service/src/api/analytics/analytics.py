import pyarrow.parquet as pq
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
import os
from api.models.models import BaseKPIs, RiskKPIs, EntropyHistogram, TopNRankings, TopNEntry, Breakdown, AnalyticsOutput


ds_base_kpi = "/home/ubuntu/dev/irontrust-analytics/data/gold/base-kpis/"
ds_risk_kpi = "/home/ubuntu/dev/irontrust-analytics/data/gold/risk-kpis/"
ds_histograms = "/home/ubuntu/dev/irontrust-analytics/data/gold/histograms/"
ds_topn = "/home/ubuntu/dev/irontrust-analytics/data/gold/topn/"
ds_breakdowns = "/home/ubuntu/dev/irontrust-analytics/data/gold/breakdowns/"


def query_analytics() -> AnalyticsOutput:
    """
    Query all analytics tables from gold layer and return structured AnalyticsOutput.
    
    Returns:
        AnalyticsOutput: Complete analytics dataset with KPIs, histograms, rankings, and breakdowns
    """
    
    # Read base KPI tables (single level partitioning: tenant, event_date)
    base_kpi_table = pq.read_table(ds_base_kpi)
    risk_kpi_table = pq.read_table(ds_risk_kpi)
    
    # Read entropy histograms with partition detection
    # Partition structure: tenant=X/event_date=Y/entropy_type=Z/
    histograms_table = pa.table({})
    if os.path.isdir(ds_histograms):
        try:
            # Use pyarrow.dataset for automatic partition discovery
            dataset = ds.dataset(
                ds_histograms,
                format='parquet',
                partitioning='hive'
            )
            histograms_table = dataset.to_table()
        except Exception as e:
            print(f"Warning: Failed to read histograms directory: {e}")
    
    # Read top-N rankings with partition detection
    # Partition structure: tenant=X/event_date=Y/topN_type=Z/
    topn_table = pa.table({})
    if os.path.isdir(ds_topn):
        try:
            dataset = ds.dataset(
                ds_topn,
                format='parquet',
                partitioning='hive'
            )
            topn_table = dataset.to_table()
        except Exception as e:
            print(f"Warning: Failed to read topn directory: {e}")
    
    # Read breakdowns with partition detection
    # Partition structure: tenant=X/event_date=Y/breakdown_type=Z/
    breakdowns_table = pa.table({})
    if os.path.isdir(ds_breakdowns):
        try:
            dataset = ds.dataset(
                ds_breakdowns,
                format='parquet',
                partitioning='hive'
            )
            breakdowns_table = dataset.to_table()
        except Exception as e:
            print(f"Warning: Failed to read breakdowns directory: {e}")

    # Convert first row of base KPI table
    base_kpi_record = {
        col: base_kpi_table.column(col)[0].as_py()
        for col in base_kpi_table.schema.names
    }
    
    # Convert first row of risk KPI table
    risk_kpi_record = {
        col: risk_kpi_table.column(col)[0].as_py()
        for col in risk_kpi_table.schema.names
    }

    # Convert histogram rows
    histograms = []
    if histograms_table.num_rows > 0:
        for i, row in enumerate(histograms_table.to_pylist()):
            try:
                # Ensure partition columns are present
                if 'tenant' not in row or 'event_date' not in row or 'entropy_type' not in row:
                    print(f"Warning: Skipping histogram row {i} - missing partition columns. Row: {row}")
                    continue
                histograms.append(EntropyHistogram(**row))
            except Exception as e:
                print(f"Warning: Failed to parse histogram row {i}: {e}")

    # Convert top-N ranking rows
    rankings = []
    if topn_table.num_rows > 0:
        # Separate aggregated rows (topN is list) and individual rows for high_entropy
        aggregated_rows = []
        high_entropy_rows = []
        for row in topn_table.to_pylist():
            if row.get('topN') is not None and isinstance(row.get('topN'), list):
                aggregated_rows.append(row)
            elif row.get('topN_type') == 'high_entropy' and row.get('topN') is None:
                high_entropy_rows.append(row)
        
        # Process aggregated rows
        for row in aggregated_rows:
            try:
                print(f"Processing topn row: topN_type={row.get('topN_type')}, topN length={len(row.get('topN', []))}")
                # Ensure partition columns are present
                if 'tenant' not in row or 'event_date' not in row:
                    print(f"Warning: Skipping topN row - missing partition columns. Row keys: {list(row.keys())}")
                    continue
                
                # Convert topN list to TopNEntry
                topn_entries = [TopNEntry(**item) for item in row['topN']]
                rankings.append(TopNRankings(
                    tenant=row['tenant'],
                    event_date=row['event_date'],
                    topN=topn_entries,
                    topN_type=row['topN_type']
                ))
            except Exception as e:
                print(f"Warning: Failed to parse topn row: {e}")
        
        # Process high_entropy individual rows
        if high_entropy_rows:
            try:
                # Get tenant and event_date from first row
                tenant = high_entropy_rows[0].get('tenant')
                event_date = high_entropy_rows[0].get('event_date')
                
                if tenant and event_date:
                    # Group by qname, aggregate query_count and max entropy
                    from collections import defaultdict
                    grouped = defaultdict(lambda: {'query_count': 0, 'entropy': 0})
                    for row in high_entropy_rows:
                        qname = row.get('qname', '')
                        query_count = row.get('query_frequency', 0)
                        entropy = row.get('qname_entropy', 0)
                        grouped[qname]['query_count'] += query_count
                        grouped[qname]['entropy'] = max(grouped[qname]['entropy'], entropy)
                    
                    # Convert to list and sort by entropy descending
                    aggregated_list = [
                        {'qname': qname, 'query_count': data['query_count'], 'entropy': data['entropy']}
                        for qname, data in grouped.items()
                    ]
                    aggregated_list.sort(key=lambda x: x['entropy'], reverse=True)
                    
                    # Take top 10
                    top_aggregated = aggregated_list[:10]
                    
                    # Create TopNEntry list
                    topn_entries = []
                    for i, item in enumerate(top_aggregated, 1):
                        entry = TopNEntry(
                            rank=i,
                            name=item['qname'],
                            query_count=item['query_count'],
                            entropy=item['entropy']
                        )
                        topn_entries.append(entry)
                    
                    rankings.append(TopNRankings(
                        tenant=tenant,
                        event_date=event_date,
                        topN=topn_entries,
                        topN_type='high_entropy'
                    ))
            except Exception as e:
                print(f"Warning: Failed to process high_entropy rows: {e}")

    # Convert breakdown rows
    breakdowns = []
    if breakdowns_table.num_rows > 0:
        for i, row in enumerate(breakdowns_table.to_pylist()):
            try:
                # Ensure partition columns are present
                if 'tenant' not in row or 'event_date' not in row or 'breakdown_type' not in row:
                    print(f"Warning: Skipping breakdown row {i} - missing partition columns. Row keys: {list(row.keys())}")
                    continue
                breakdowns.append(Breakdown(**row))
            except Exception as e:
                print(f"Warning: Failed to parse breakdown row {i}: {e}")

    return AnalyticsOutput(
        base_kpis=BaseKPIs(**base_kpi_record),
        risk_kpis=RiskKPIs(**risk_kpi_record),
        histograms=histograms,
        rankings=rankings,
        breakdowns=breakdowns
    )