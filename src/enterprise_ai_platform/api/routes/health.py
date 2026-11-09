"""
Health-check endpoint router: liveness and readiness probes.
"""
from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Service health check")
async def health_check() -> dict[str, str]:
    """Liveness probe indicating API service availability."""
    return {"status": "healthy"}
