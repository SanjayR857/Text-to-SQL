"""
Request identity models representing authenticated caller principals.
"""
from pydantic import BaseModel, ConfigDict, Field


class RequestIdentity(BaseModel):
    """
    Caller identity established during request authentication.

    Decoupled from authorization, user tables, and database persistence.
    Can be populated by the development header (x-dev-user-email) or by
    future verified Entra ID JWT claims.
    """

    model_config = ConfigDict(frozen=True)

    email: str = Field(..., description="Canonical lowercase email address of the caller")
    auth_method: str = Field(
        default="dev_header",
        description="Mechanism used to establish identity (e.g., 'dev_header', 'entra_id_jwt')",
    )
