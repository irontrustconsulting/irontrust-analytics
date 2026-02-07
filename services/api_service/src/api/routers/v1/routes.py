from fastapi import APIRouter, Request, HTTPException, Query
# from .query_model_map import TEMPLATE_RESULT_MODELS

from app.models.query_results import (
    AvgEntropyRow,
    NxDomainRow,
    QnameLengthRow,
    TopDomainsRow,
    TopQueryTypesRow,
    TopNClientsRow,
)

TEMPLATE_RESULT_MODELS = {
    "avg_entropy": AvgEntropyRow,
    "nx_domain": NxDomainRow,
    "qname_length": QnameLengthRow,
    "top_domains": TopDomainsRow,
    "top_query_types": TopQueryTypesRow,
    "topn_clients": TopNClientsRow,
}

DEFAULT_MAX_LIMIT = 10_000

router = APIRouter()

# ------------------------------------------------------------
# 1) LIST AVAILABLE ANALYTIC TEMPLATES
# ------------------------------------------------------------
@router.get("/{tenant_id}/analytics/templates")
def list_templates(tenant_id: str, request: Request):
    return request.app.state.registry.list_templates()


# ------------------------------------------------------------
# 2) GET DETAILS FOR A SPECIFIC TEMPLATE
# ------------------------------------------------------------
@router.get("/{tenant_id}/analytics/templates/{template_id}")
def get_template_details(tenant_id: str, template_id: str, request: Request):
    tpl = request.app.state.registry.get_template(template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return tpl.model_dump()


# ------------------------------------------------------------
# 3) RUN A TEMPLATE & RETURN TYPED RESULTS
# ------------------------------------------------------------
@router.get("/{tenant_id}/analytics/run/{template_id}")
def run_template(
    tenant_id: str,
    template_id: str,
    request: Request,
    limit: int | None = Query(
        default=None,
        gt=0,
        le=DEFAULT_MAX_LIMIT,
        description="Max number of items to return",
    ),
):

    registry = request.app.state.registry
    config = request.app.state.config
    executor = request.app.state.executor

    # ---- 1) Look up template ----
    tpl = registry.get_template(template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")

    # ---- 2) Look up the result model for this template ----
    if template_id not in TEMPLATE_RESULT_MODELS:
        raise HTTPException(
            status_code=500,
            detail=f"No Pydantic result model defined for template '{template_id}'."
        )

    ResultModel = TEMPLATE_RESULT_MODELS[template_id]

    # ---- 3) SQL Jinja context ----
    context = {
        "ATHENA_DATABASE": config.athena_database,
        "ATHENA_TABLE": config.athena_table,
        "tenant": tenant_id,
        "limit": limit if limit is not None else config.default_limit,
    }

    # ---- 4) Run Athena query ----
    raw_rows = executor.run_query_and_wait(
        sql_template=tpl.sql,
        context=context,
        database=config.athena_database,
        output_bucket=config.athena_output_bucket,
    )

    # ---- 5) Validate results with Pydantic ----
    typed_results = [ResultModel(**row).model_dump() for row in raw_rows]

    return {
        "tenant": tenant_id,
        "template": tpl.metadata.id,
        "results": typed_results
    }
