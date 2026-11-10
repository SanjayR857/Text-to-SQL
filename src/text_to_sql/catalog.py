"""
Curated enterprise schema metadata catalog and hybrid enrichment service.

Enriches introspected live database schemas with domain descriptions,
business synonyms, sample values, and sensitivity classifications while
strictly preserving physical database authority.
"""
from dataclasses import dataclass, field
from typing import Any

from text_to_sql.schema import (
    DatabaseSchemaEntity,
)
from text_to_sql.metadata import (
    ColumnMetadataEntity,
    TableMetadataEntity,
)


@dataclass(frozen=True)
class ColumnBusinessMetadata:
    """
    Curated business metadata for a database column.
    """

    description: str | None = None
    synonyms: list[str] = field(default_factory=list)
    sample_values: list[str] = field(default_factory=list)
    sensitivity: str | None = None


@dataclass(frozen=True)
class TableBusinessMetadata:
    """
    Curated business metadata for a database table.
    """

    description: str | None = None
    synonyms: list[str] = field(default_factory=list)
    columns: dict[str, ColumnBusinessMetadata] = field(default_factory=dict)


# Authoritative pre-configured metadata matching enterprise schema specifications
DEFAULT_ENTERPRISE_CATALOG: dict[str, TableBusinessMetadata] = {
    "employeeinformation": TableBusinessMetadata(
        description="Master employee profile directory storing employee identities, titles, designations, and corporate email addresses.",
        synonyms=["employee", "staff", "workforce", "personnel", "team member", "headcount", "people"],
        columns={
            "employeemailid": ColumnBusinessMetadata(
                description="Unique corporate email address of the employee; primary identifier across platform tables.",
                synonyms=["email", "employee email", "worker email", "corporate email", "user email"],
                sample_values=["john.doe@company.com", "jane.smith@company.com"],
                sensitivity="INTERNAL",
            ),
            "employeename": ColumnBusinessMetadata(
                description="Full legal name of the employee.",
                synonyms=["name", "full name", "staff name", "worker name"],
                sample_values=["John Doe", "Jane Smith"],
                sensitivity="INTERNAL",
            ),
            "designation": ColumnBusinessMetadata(
                description="Current job title or designation of the employee.",
                synonyms=["job title", "title", "role title", "position"],
                sample_values=["Senior Consultant", "Lead Architect", "Developer"],
                sensitivity="INTERNAL",
            ),
            "verticalcode": ColumnBusinessMetadata(
                description="Code of the business vertical the employee is primarily assigned to.",
                synonyms=["vertical", "department code", "practice code"],
                sample_values=["CHAIO", "CHDLO", "CHTAO", "CHENO"],
                sensitivity="INTERNAL",
            ),
            "pannumber": ColumnBusinessMetadata(
                description="Permanent Account Number (PAN) tax identifier.",
                synonyms=["tax id", "pan", "pan card"],
                sample_values=["ABCDE1234F"],
                sensitivity="CONFIDENTIAL",
            ),
            "passportnumber": ColumnBusinessMetadata(
                description="Government passport identification number.",
                synonyms=["passport", "travel document"],
                sample_values=["Z1234567"],
                sensitivity="CONFIDENTIAL",
            ),
            "fixedctc": ColumnBusinessMetadata(
                description="Annual fixed Cost to Company compensation figure.",
                synonyms=["fixed pay", "base salary", "annual base"],
                sample_values=["1500000"],
                sensitivity="CONFIDENTIAL",
            ),
            "variablectc": ColumnBusinessMetadata(
                description="Annual performance-linked variable incentive compensation figure.",
                synonyms=["variable pay", "bonus target", "incentive pay"],
                sample_values=["300000"],
                sensitivity="CONFIDENTIAL",
            ),
            "currentctc": ColumnBusinessMetadata(
                description="Total gross current Cost to Company (fixed plus variable).",
                synonyms=["total salary", "gross compensation", "ctc", "package"],
                sample_values=["1800000"],
                sensitivity="CONFIDENTIAL",
            ),
        },
    ),
    "officeattendance": TableBusinessMetadata(
        description="Daily badge-swipe and office attendance records tracking employee presence, entry/exit timestamps, and working hours.",
        synonyms=["attendance", "office presence", "badge swipes", "swipe logs", "work hours", "in-office days"],
        columns={
            "employeemailid": ColumnBusinessMetadata(
                description="Corporate email of the employee whose attendance was recorded.",
                synonyms=["email", "employee email", "attendee email"],
                sample_values=["john.doe@company.com"],
                sensitivity="INTERNAL",
            ),
            "attendancedate": ColumnBusinessMetadata(
                description="Calendar date of the attendance record.",
                synonyms=["date", "work date", "swipe date", "attendance day"],
                sample_values=["2026-11-10"],
                sensitivity="INTERNAL",
            ),
            "firstintime": ColumnBusinessMetadata(
                description="Timestamp of the employee's first badge punch-in of the day.",
                synonyms=["entry time", "check-in time", "first punch", "in time"],
                sample_values=["09:15:00"],
                sensitivity="INTERNAL",
            ),
            "lastouttime": ColumnBusinessMetadata(
                description="Timestamp of the employee's last badge punch-out of the day.",
                synonyms=["exit time", "check-out time", "last punch", "out time"],
                sample_values=["18:45:00"],
                sensitivity="INTERNAL",
            ),
            "totalhours": ColumnBusinessMetadata(
                description="Total computed in-office working hours for the date.",
                synonyms=["hours worked", "duration", "shift duration", "daily hours"],
                sample_values=["8.5", "9.0"],
                sensitivity="INTERNAL",
            ),
        },
    ),
    "scoreboard": TableBusinessMetadata(
        description="Executive quarterly and annual performance leaderboards and composite rating ranks across firm personnel.",
        synonyms=["rankings", "leaderboard", "performance scores", "executive rankings", "appraisal rank"],
        columns={
            "employeemailid": ColumnBusinessMetadata(
                description="Corporate email of the evaluated employee.",
                synonyms=["email", "employee email"],
                sample_values=["john.doe@company.com"],
                sensitivity="CONFIDENTIAL",
            ),
            "quarter": ColumnBusinessMetadata(
                description="Evaluation quarter (e.g., Q1, Q2, Q3, Q4).",
                synonyms=["eval quarter", "fiscal quarter"],
                sample_values=["Q1", "Q2", "Q3", "Q4"],
                sensitivity="CONFIDENTIAL",
            ),
            "year": ColumnBusinessMetadata(
                description="Evaluation appraisal calendar year.",
                synonyms=["fiscal year", "appraisal year"],
                sample_values=["2025", "2026"],
                sensitivity="CONFIDENTIAL",
            ),
            "overallscore": ColumnBusinessMetadata(
                description="Aggregated final performance score.",
                synonyms=["final rating", "composite score", "total score"],
                sample_values=["4.25", "4.80"],
                sensitivity="CONFIDENTIAL",
            ),
            "rank": ColumnBusinessMetadata(
                description="Relative performance rank within the cohort or practice.",
                synonyms=["position", "leaderboard rank", "standing"],
                sample_values=["1", "5", "12"],
                sensitivity="CONFIDENTIAL",
            ),
        },
    ),
    "projectname": TableBusinessMetadata(
        description="Master project engagements and client accounts directory.",
        synonyms=["projects", "client engagements", "accounts", "contracts", "delivery projects"],
        columns={
            "id": ColumnBusinessMetadata(
                description="Unique primary key identifier for the project.",
                synonyms=["project id", "engagement id"],
                sample_values=["PRJ-001", "PRJ-002"],
                sensitivity="INTERNAL",
            ),
            "projectname": ColumnBusinessMetadata(
                description="Official title or commercial name of the project.",
                synonyms=["name", "project title", "engagement name"],
                sample_values=["Alpha Cloud Transformation", "Apollo AI Migration"],
                sensitivity="INTERNAL",
            ),
            "verticalcode": ColumnBusinessMetadata(
                description="Business vertical responsible for project delivery.",
                synonyms=["vertical", "practice code"],
                sample_values=["CHAIO", "CHDLO"],
                sensitivity="INTERNAL",
            ),
            "contractvalue": ColumnBusinessMetadata(
                description="Total contracted financial monetary value of the project engagement.",
                synonyms=["contract value", "revenue", "deal size", "commercial value", "budget"],
                sample_values=["5000000", "12000000"],
                sensitivity="RESTRICTED",
            ),
            "pricingmodel": ColumnBusinessMetadata(
                description="Billing contract model (e.g., Time & Materials, Fixed Price).",
                synonyms=["billing model", "commercial structure"],
                sample_values=["Time & Materials", "Fixed Price"],
                sensitivity="RESTRICTED",
            ),
            "teamleadmails": ColumnBusinessMetadata(
                description="Corporate email addresses of designated technical team leads on the project.",
                synonyms=["leads", "technical leads", "team leads"],
                sample_values=["lead@company.com"],
                sensitivity="INTERNAL",
            ),
            "pmomail": ColumnBusinessMetadata(
                description="Corporate email of the Project Management Office (PMO) representative.",
                synonyms=["pmo lead", "pmo email", "project manager email"],
                sample_values=["pmo@company.com"],
                sensitivity="INTERNAL",
            ),
        },
    ),
    "projectdetail": TableBusinessMetadata(
        description="Resource staffing allocations, active assignments, and roll-on/roll-off schedules on delivery projects.",
        synonyms=["staffing", "allocations", "project assignments", "resource allocations", "team rosters"],
        columns={
            "projectid": ColumnBusinessMetadata(
                description="Foreign key identifier referencing the parent project in ProjectName.",
                synonyms=["project id", "engagement id"],
                sample_values=["PRJ-001"],
                sensitivity="INTERNAL",
            ),
            "resourcemailid": ColumnBusinessMetadata(
                description="Corporate email address of the allocated team resource.",
                synonyms=["employee email", "resource email", "staff email"],
                sample_values=["john.doe@company.com"],
                sensitivity="INTERNAL",
            ),
            "allocationpercentage": ColumnBusinessMetadata(
                description="Percentage of full-time working capacity committed to this project.",
                synonyms=["allocation", "capacity percent", "staffing load"],
                sample_values=["50", "100"],
                sensitivity="INTERNAL",
            ),
            "billingrate": ColumnBusinessMetadata(
                description="Commercial hourly or daily client billing rate for the resource.",
                synonyms=["bill rate", "client rate", "chargeout rate"],
                sample_values=["120.00", "250.00"],
                sensitivity="RESTRICTED",
            ),
        },
    ),
    "demand": TableBusinessMetadata(
        description="Open talent requisitions and recruitment demands for staffing project and vertical capabilities.",
        synonyms=["hiring demand", "requisitions", "open positions", "staffing requirements", "vacancies"],
        columns={
            "id": ColumnBusinessMetadata(
                description="Unique identifier for the demand requisition.",
                synonyms=["demand id", "requisition id"],
                sample_values=["DEM-101"],
                sensitivity="INTERNAL",
            ),
            "verticalcode": ColumnBusinessMetadata(
                description="Vertical code requesting headcount.",
                synonyms=["vertical", "hiring practice"],
                sample_values=["CHAIO"],
                sensitivity="INTERNAL",
            ),
            "requiredskills": ColumnBusinessMetadata(
                description="Target primary technical competencies and skill requirements.",
                synonyms=["skills", "tech stack", "competencies"],
                sample_values=["Python, FastAPI, PostgreSQL", "React, TypeScript"],
                sensitivity="INTERNAL",
            ),
            "openpositions": ColumnBusinessMetadata(
                description="Number of open positions needed for this requisition.",
                synonyms=["headcount needed", "vacancies count"],
                sample_values=["2", "5"],
                sensitivity="INTERNAL",
            ),
            "status": ColumnBusinessMetadata(
                description="Current recruitment workflow status.",
                synonyms=["demand state", "hiring status"],
                sample_values=["OPEN", "IN_PROGRESS", "CLOSED"],
                sensitivity="INTERNAL",
            ),
        },
    ),
    "ratingcomment": TableBusinessMetadata(
        description="Qualitative performance feedback and narrative evaluation comments entered during appraisal reviews.",
        synonyms=["appraisal comments", "performance feedback", "review notes", "evaluation comments"],
        columns={
            "id": ColumnBusinessMetadata(
                description="Unique identifier for the appraisal comment record.",
                synonyms=["comment id"],
                sample_values=["RC-901"],
                sensitivity="INTERNAL",
            ),
            "rateeemail": ColumnBusinessMetadata(
                description="Corporate email of the employee who was evaluated.",
                synonyms=["ratee", "evaluated employee email"],
                sample_values=["john.doe@company.com"],
                sensitivity="INTERNAL",
            ),
            "createdby": ColumnBusinessMetadata(
                description="Corporate email of the author or evaluator who wrote the comment.",
                synonyms=["author", "evaluator email", "rater email"],
                sample_values=["lead@company.com"],
                sensitivity="INTERNAL",
            ),
            "comment": ColumnBusinessMetadata(
                description="Narrative evaluation text summarizing qualitative performance.",
                synonyms=["feedback text", "review commentary", "remarks"],
                sample_values=["Demonstrated strong initiative and high technical quality."],
                sensitivity="INTERNAL",
            ),
        },
    ),
    "vertical": TableBusinessMetadata(
        description="Master organizational directory of platform business verticals and practice areas.",
        synonyms=["business verticals", "practices", "divisions", "departments", "units"],
        columns={
            "verticalcode": ColumnBusinessMetadata(
                description="Primary uppercase short code identifying the vertical (e.g. CHAIO, CHDLO).",
                synonyms=["code", "vertical abbreviation"],
                sample_values=["CHAIO", "CHDLO", "CHTAO", "CHENO"],
                sensitivity="PUBLIC",
            ),
            "verticalname": ColumnBusinessMetadata(
                description="Human-readable business name of the vertical.",
                synonyms=["name", "department name", "practice name"],
                sample_values=["Central AI Office", "Digital Leadership Office"],
                sensitivity="PUBLIC",
            ),
            "area": ColumnBusinessMetadata(
                description="Organizational grouping area (CentralApplication or IndividualModule).",
                synonyms=["area group", "module tier"],
                sample_values=["CentralApplication", "IndividualModule"],
                sensitivity="PUBLIC",
            ),
            "isactive": ColumnBusinessMetadata(
                description="Whether the business vertical is currently active.",
                synonyms=["active status", "enabled"],
                sample_values=["true", "false"],
                sensitivity="PUBLIC",
            ),
        },
    ),
    "roleassignment": TableBusinessMetadata(
        description="User security role bindings associating platform principals with business verticals.",
        synonyms=["roles", "user roles", "access rights", "permissions", "role allocations"],
        columns={
            "id": ColumnBusinessMetadata(
                description="Unique identifier for the role assignment record.",
                synonyms=["assignment id"],
                sample_values=["RA-001"],
                sensitivity="INTERNAL",
            ),
            "email": ColumnBusinessMetadata(
                description="Corporate email address of the assigned platform user.",
                synonyms=["user email", "principal email"],
                sample_values=["john.doe@company.com"],
                sensitivity="INTERNAL",
            ),
            "role": ColumnBusinessMetadata(
                description="Assigned platform Role enum value (e.g., ADMIN, EP, CHIEF, LEAD, DEV, CON).",
                synonyms=["security role", "role code"],
                sample_values=["ADMIN", "EP", "CHIEF", "LEAD", "DEV", "CON"],
                sensitivity="INTERNAL",
            ),
            "verticalcode": ColumnBusinessMetadata(
                description="Business vertical code bound to this role assignment.",
                synonyms=["vertical", "department"],
                sample_values=["CHAIO", "CHDLO"],
                sensitivity="INTERNAL",
            ),
        },
    ),
}


class EnterpriseMetadataCatalog:
    """
    Curated metadata repository providing domain enrichment for introspected schemas.

    Decorates physical database facts with business descriptions, synonyms, sample values,
    and data sensitivity classifications without ever creating fictitious physical columns.
    """

    def __init__(
        self,
        catalog: dict[str, TableBusinessMetadata] | None = None,
    ) -> None:
        """
        Initialize catalog with default or custom business metadata definitions.

        Args:
            catalog: Optional dictionary mapping lowercase table names to TableBusinessMetadata.
        """
        self._catalog: dict[str, TableBusinessMetadata] = (
            dict(catalog) if catalog is not None else dict(DEFAULT_ENTERPRISE_CATALOG)
        )

    def register_table_metadata(
        self,
        table_name: str,
        description: str | None = None,
        synonyms: list[str] | None = None,
        columns: dict[str, ColumnBusinessMetadata] | None = None,
    ) -> None:
        """
        Register or override curated metadata for a specific database table.

        Args:
            table_name: Canonical or lowercase table name.
            description: Curated business description.
            synonyms: Business synonyms.
            columns: Dictionary of column metadata keyed by lowercase column name.
        """
        key = table_name.strip().lower()
        self._catalog[key] = TableBusinessMetadata(
            description=description,
            synonyms=list(synonyms) if synonyms is not None else [],
            columns=dict(columns) if columns is not None else {},
        )

    def get_table_metadata(self, table_name: str) -> TableBusinessMetadata | None:
        """
        Retrieve curated business metadata for a table case-insensitively.

        Args:
            table_name: Table name to look up.
        """
        if not table_name:
            return None
        return self._catalog.get(table_name.strip().lower())

    def enrich_schema(self, schema: DatabaseSchemaEntity) -> DatabaseSchemaEntity:
        """
        Decorate an introspected DatabaseSchemaEntity with curated business metadata.

        Strict Invariants:
            1. Physical facts from introspection (columns, data types, keys) are immutable.
            2. Catalog entries for tables or columns absent from the physical database
               are NEVER added.
            3. Curated descriptions, synonyms, and sensitivity decorate existing entities.

        Args:
            schema: Introspected DatabaseSchemaEntity.

        Returns:
            Enriched DatabaseSchemaEntity with curated business annotations.
        """
        enriched_tables: dict[str, TableMetadataEntity] = {}

        for tbl_key, table_entity in schema.tables.items():
            business_tbl = self.get_table_metadata(tbl_key)

            # Determine table-level business attributes
            tbl_desc = table_entity.description or (
                business_tbl.description if business_tbl else None
            )
            tbl_synonyms = list(table_entity.synonyms)
            if business_tbl and business_tbl.synonyms:
                for s in business_tbl.synonyms:
                    if s not in tbl_synonyms:
                        tbl_synonyms.append(s)

            # Enrich columns
            enriched_columns: dict[str, ColumnMetadataEntity] = {}
            for col_key, col_entity in table_entity.columns.items():
                business_col: ColumnBusinessMetadata | None = None
                if business_tbl and col_key in business_tbl.columns:
                    business_col = business_tbl.columns[col_key]

                col_desc = col_entity.description or (
                    business_col.description if business_col else None
                )
                col_sensitivity = col_entity.sensitivity or (
                    business_col.sensitivity if business_col else None
                )

                col_synonyms = list(col_entity.synonyms)
                if business_col and business_col.synonyms:
                    for s in business_col.synonyms:
                        if s not in col_synonyms:
                            col_synonyms.append(s)

                col_samples = list(col_entity.sample_values)
                if business_col and business_col.sample_values:
                    for smp in business_col.sample_values:
                        if smp not in col_samples:
                            col_samples.append(smp)

                enriched_col = col_entity.model_copy(
                    update={
                        "description": col_desc,
                        "synonyms": col_synonyms,
                        "sample_values": col_samples,
                        "sensitivity": col_sensitivity,
                    }
                )
                enriched_columns[col_key] = enriched_col

            enriched_table = table_entity.model_copy(
                update={
                    "description": tbl_desc,
                    "synonyms": tbl_synonyms,
                    "columns": enriched_columns,
                }
            )
            enriched_tables[tbl_key] = enriched_table

        return schema.model_copy(update={"tables": enriched_tables})
