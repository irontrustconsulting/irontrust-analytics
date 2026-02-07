from fastapi import APIRouter
from app.db.athena import AthenaExecutor as Executor
from jinja2 import Template

router = APIRouter()

@router.get("/")
def read_tenants():
    return{
            "tenant_1": "tenant-demo-1",
            "tenant_2": "tenant-demo-2"  
    }

@router.get("/{tenant_id}")
def read_tenant(tenant_id):
    return { "tenant_id": f"{tenant_id}"}

@router.get("/{tenant_id}/analytics/{template_id}/run")
def read_tenant(tenant_id):
    context = {
        "athena_output_bucket": "irontrust-athena",
        "ATHENA_DATABASE": "analyticsdb",
        "ATHENA_TABLE": "irontrust_analytics_gold",
        "tenant": tenant_id,
        "limit": 25
    }
    sql_template = "SELECT qname, AVG(entropy) AS avg_entropy, COUNT(*) AS query_count FROM \"AwsDataCatalog\".\"{{ ATHENA_DATABASE }}\".\"{{ ATHENA_TABLE }}\" WHERE tenant = '{{ tenant }}' GROUP BY qname ORDER BY avg_entropy DESC LIMIT {{ limit }};"
    athena_output_bucket =  "irontrust-athena"

    executor = Executor(region_name="eu-west-2")
    result = executor.run_query_and_wait(sql_template=sql_template,context=context,output_bucket=athena_output_bucket, database="analyticsdb")
    
    return { "query_result": result}