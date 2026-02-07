# api/models.py
from pydantic import BaseModel
from typing import List, Dict
'''                                                                              
root
 |-- total_queries: long (nullable = true)
 |-- unique_qnames: long (nullable = true)
 |-- unique_root_domains: long (nullable = true)
 |-- unique_subdomains: long (nullable = true)
 |-- unique_src_ips: long (nullable = true)
 |-- avg_qname_entropy: double (nullable = true)
 |-- max_qname_entropy: double (nullable = true)
 |-- avg_subdomain_entropy: double (nullable = true)
 |-- max_subdomain_entropy: double (nullable = true)
 |-- avg_subdomain_count: double (nullable = true)
 |-- max_subdomain_count: integer (nullable = true)
 |-- top_qnames: array (nullable = true)
 |    |-- element: struct (containsNull = true)
 |    |    |-- qname: string (nullable = true)
 |    |    |-- query_count: long (nullable = true)
 |-- rcode_breakdown: array (nullable = true)
 |    |-- element: struct (containsNull = true)
 |    |    |-- rcode: integer (nullable = true)
 |    |    |-- count: long (nullable = true)
 |-- qtype_breakdown: array (nullable = true)
 |    |-- element: struct (containsNull = true)
 |    |    |-- qtype: integer (nullable = true)
 |    |    |-- count: long (nullable = true)
 |-- qname_entropy_histogram: array (nullable = true)
 |    |-- element: struct (containsNull = true)
 |    |    |-- bin: string (nullable = true)
 |    |    |-- count: long (nullable = true)
 |-- subdomain_entropy_histogram: array (nullable = true)
 |    |-- element: struct (containsNull = true)
 |    |    |-- bin: string (nullable = true)
 |    |    |-- count: long (nullable = true)
 |-- top_root_domains: array (nullable = true)
 |    |-- element: struct (containsNull = true)
 |    |    |-- root_domain: string (nullable = true)
 |    |    |-- query_count: long (nullable = true)
 |    |    |-- rank: integer (nullable = true)
 |-- high_entropy_query_count: long (nullable = true)
 |-- high_entropy_query_ratio: double (nullable = true)
 |-- max_entropy_qname: string (nullable = true)
 |-- high_entropy_qnames_topN: array (nullable = true)
 |    |-- element: struct (containsNull = true)
 |    |    |-- qname: string (nullable = true)
 |    |    |-- entropy: double (nullable = true)
 |    |    |-- query_count: long (nullable = true)
 |-- nxdomain_count: long (nullable = true)
 |-- nxdomain_ratio: double (nullable = true)
 |-- alert_high_entropy: boolean (nullable = true)
 |-- alert_nxdomain: boolean (nullable = true)
 |-- tenant: string (nullable = true)
 |-- event_date: date (nullable = true)

1
'''

class TemplateMetaData(BaseModel):
    id: str
    name: str
    description: str
    version: float
    category: str

class QueryTemplate(BaseModel):
    sql: str
    metadata: TemplateMetaData

class Templates(BaseModel):
    id: str
    name: str

class Histogram(BaseModel):
    bins: List[str]
    counts: List[int]


class TopItem(BaseModel):
    label: str
    count: int

class AnalyticsResponse(BaseModel):
    tenant_id: str
    event_date: str

    totals: Dict[str, int]

    qname_entropy_histogram: Histogram
    subdomain_entropy_histogram: Histogram

    top_qnames: List[TopItem]
    top_rcodes: List[TopItem]
    top_qtypes: List[TopItem]

class TemplateRegistry(BaseModel):
    registry: list[QueryTemplate]

    def get_template(self, template_id: str) -> QueryTemplate | None:
        for tpl in self.registry:
            if tpl.metadata.id == template_id:
                return tpl
        return None

    def list_templates(self) -> list[str]:
        # return [tpl.metadata.name for tpl in self.registry]
        return [Templates(id=tpl.metadata.id, name=tpl.metadata.name) for tpl in self.registry]


