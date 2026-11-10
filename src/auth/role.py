"""
Role and Area domain enums matching the PostgreSQL RBAC schema.
"""
from enum import StrEnum


class Role(StrEnum):
    """
    Platform roles representing organizational positions and access tiers.
    Synchronized with PostgreSQL enum type "Role".
    """

    ADMIN = "ADMIN"
    DEV = "DEV"
    EP = "EP"
    ES = "ES"
    CHIEF = "CHIEF"
    LEAD = "LEAD"
    CON = "CON"


class Area(StrEnum):
    """
    Vertical organizational grouping.
    Synchronized with PostgreSQL enum type "Area".
    """

    CentralApplication = "CentralApplication"
    IndividualModule = "IndividualModule"
