# API package router aggregation
from fastapi import APIRouter
from backend.app.api.departments import router as departments_router
from backend.app.api.requisitions import router as requisitions_router
from backend.app.api.candidates import router as candidates_router
from backend.app.api.applications import router as applications_router
from backend.app.api.interviews import router as interviews_router
from backend.app.api.interviewers import router as interviewers_router
from backend.app.api.feedback import router as feedback_router
from backend.app.api.offers import router as offers_router
from backend.app.api.analytics import router as analytics_router
from backend.app.api.anomalies import router as anomalies_router
from backend.app.api.audit import router as audit_router
from backend.app.api.validation import router as validation_router
from backend.app.api.skills import router as skills_router

api_router = APIRouter(prefix="/api")

api_router.include_router(departments_router)
api_router.include_router(requisitions_router)
api_router.include_router(candidates_router)
api_router.include_router(applications_router)
api_router.include_router(interviews_router)
api_router.include_router(interviewers_router)
api_router.include_router(feedback_router)
api_router.include_router(offers_router)
api_router.include_router(analytics_router)
api_router.include_router(anomalies_router)
api_router.include_router(audit_router)
api_router.include_router(validation_router)
api_router.include_router(skills_router)
