# api/models/query_results.py
from pydantic import BaseModel
from typing import Optional


# 1️⃣ avg_entropy
class AvgEntropyRow(BaseModel):
    qname: Optional[str]
    avg_entropy: float
    query_count: int


# 2️⃣ nx_domain
class NxDomainRow(BaseModel):
    qname: Optional[str]
    nxdomain_count: int


# 3️⃣ qname_length
class QnameLengthRow(BaseModel):
    qname: Optional[str]
    qname_length: int


# 4️⃣ top_domains
class TopDomainsRow(BaseModel):
    qname: Optional[str]
    query_count: int


# 5️⃣ top_query_types
class TopQueryTypesRow(BaseModel):
    qtype: Optional[str]
    query_count: int


# 6️⃣ topn_clients
class TopNClientsRow(BaseModel):
    client_ip: Optional[str]
    query_count: int
