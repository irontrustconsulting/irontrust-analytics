from fastapi import APIRouter, HTTPException
from api.models.models import AnalyticsOutput
from api.analytics.analytics import query_analytics

router = APIRouter()

BUCKET = "irontrust-analytics-gold"


@router.get("/")
def root():
    return {
        "msg": "Welcome to Irontrust Analytics App"
    }
    

@router.get("/analytics", response_model=AnalyticsOutput)
def get_analytics() -> AnalyticsOutput:
    """
    Get complete analytics dashboard data.
    
    Returns:
        AnalyticsOutput: Complete analytics dataset including KPIs, histograms, rankings, and breakdowns
    """
    return query_analytics()

