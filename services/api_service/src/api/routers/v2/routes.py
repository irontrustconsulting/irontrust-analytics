from fastapi import APIRouter, HTTPException
from api.models.v2 import AnalyticsGoldRecord
from api.utils.s3_reader  import read_single_parquet_row

router = APIRouter()

BUCKET = "irontrust-analytics-gold"
BASE_PREFIX = "dns/daily_aggregates"


@router.get("/")
def root():
    return {
        "msg": "Welcome to Ironttrust Analytics App"
    }


@router.get(
    "/analytics",
    response_model=AnalyticsGoldRecord,
    summary="Get daily analytics for a tenant"
)
def get_analytics(tenant_id: str, event_date: str):
    prefix = (
        f"{BASE_PREFIX}/"
        f"tenant={tenant_id}/"
        f"event_date={event_date}/"
    )

    try:
        record_dict = read_single_parquet_row(
            bucket=BUCKET,
            prefix=prefix
        )

        record_dict["tenant"] = tenant_id
        record_dict["event_date"] = event_date

        # Validate + serialize via Pydantic
        return AnalyticsGoldRecord(**record_dict)

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
