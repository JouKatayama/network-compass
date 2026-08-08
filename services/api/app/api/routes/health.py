from fastapi import APIRouter, status

from app.models.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Check API liveness",
)
def health() -> HealthResponse:
    return HealthResponse()
