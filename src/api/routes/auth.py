"""
Authentication and user-context endpoint router.
"""
from fastapi import APIRouter, Depends

from api.dependencies import get_current_user_context
from schemas.auth import UserContextResponse
from rbac.identity import UserContext

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get(
    "/me",
    response_model=UserContextResponse,
    summary="Retrieve authenticated user context",
    description="Returns the resolved user context including roles, active verticals, and lead project scopes.",
)
async def get_current_user(
    context: UserContext = Depends(get_current_user_context),
) -> UserContextResponse:
    """
    Return the authenticated user's resolved context.

    Args:
        context: UserContext injected from request.state.user_context.

    Returns:
        UserContextResponse containing user_id, email, assignments, and access_scope.
    """
    return UserContextResponse(
        user_id=context.user_id,
        email=context.email,
        assignments=context.assignments,
        access_scope=context.access_scope,
    )
