"""
Declarative policy handler for standard vertical-scoped and module tables.
"""
from typing import Any

from rbac.policies.access_context import (
    AccessScope,
    ColumnPermission,
    ColumnSensitivity,
    TablePermission,
)
from rbac.policies.handlers.base_handler import (
    BasePolicyHandler,
)
from rbac.policies.predicate_spec import (
    PredicateSpec,
)
from rbac.identity.role import Role
from rbac.identity.user import UserContext

# Table classification metadata
# (table_name_lower: (canonical_name, primary_filter_type, list_of_known_columns))
# primary_filter_type: "VERTICAL", "SELF", "ADMIN_ONLY", "OPEN"
_TABLE_REGISTRY: dict[str, tuple[str, str, list[str]]] = {
    # Module 1: Core RBAC
    "vertical": ("Vertical", "OPEN", ["id", "code", "name", "area", "isActive"]),
    "roleassignment": ("RoleAssignment", "ADMIN_ONLY", ["id", "email", "verticalCode", "role"]),
    "users": ("users", "ADMIN_ONLY", ["id", "email", "name", "role", "isActive"]),
    # Module 6: Chief Goals & Recognition
    "chiefgoal": ("ChiefGoal", "VERTICAL", ["id", "verticalCode", "appraisalYearId", "title", "description", "weightage"]),
    "employeechiefareaselection": ("EmployeeChiefAreaSelection", "SELF", ["id", "employeeMailId", "appraisalYearId", "verticalCode", "status"]),
    "chiefgoalrating": ("ChiefGoalRating", "SELF", ["id", "goalId", "employeeMailId", "appraisalYearId", "quarter", "starRating"]),
    "recognition": ("Recognition", "SELF", ["id", "employeeMailId", "appraisalYearId", "quarter", "description", "bonusPoints"]),
    "recognitionpolicy": ("RecognitionPolicy", "OPEN", ["id", "recognitionTeamPercent", "maxRecognitionPerChiefPerQuarter"]),
    "badgeofhonoraward": ("BadgeOfHonorAward", "SELF", ["id", "employeeMailId", "badgeCode", "appraisalYearId", "conferredBy"]),
    "quarterexclusion": ("QuarterExclusion", "SELF", ["id", "employeeMailId", "appraisalYearId", "quarter", "reason"]),
    # Module 7: Partner & EM Goals
    "partnergoal": ("PartnerGoal", "VERTICAL", ["id", "verticalCode", "appraisalYearId", "title", "description", "weightage"]),
    "partnergoalrating": ("PartnerGoalRating", "VERTICAL", ["id", "goalId", "chiefEmail", "verticalCode", "quarter", "starRating"]),
    "partnergoalacceptance": ("PartnerGoalAcceptance", "VERTICAL", ["id", "verticalCode", "appraisalYearId", "acceptedBy"]),
    "emgoal": ("EmGoal", "VERTICAL", ["id", "verticalCode", "appraisalYearId", "title", "description", "weightage"]),
    "emgoalrating": ("EmGoalRating", "VERTICAL", ["id", "goalId", "employeeMailId", "verticalCode", "quarter", "starRating"]),
    "emgoalacceptance": ("EmGoalAcceptance", "VERTICAL", ["id", "verticalCode", "appraisalYearId", "employeeMailId"]),
    # Module 8: KPI & Delivery Appraisal
    "kpirole": ("KpiRole", "OPEN", ["id", "label", "code", "sortOrder", "active"]),
    "appraisalyear": ("AppraisalYear", "OPEN", ["id", "yearLabel", "startDate", "endDate", "isActive"]),
    "quarterlyratingwindow": ("QuarterlyRatingWindow", "OPEN", ["id", "module", "appraisalYearId", "quarter", "isPublished"]),
    "kpigoal": ("KpiGoal", "OPEN", ["id", "projectId", "appraisalYearId", "title", "description", "weightage"]),
    "kpigoalrole": ("KpiGoalRole", "OPEN", ["id", "goalId", "roleId"]),
    "employeegoalassignment": ("EmployeeGoalAssignment", "SELF", ["id", "employeeMailId", "projectId", "appraisalYearId", "status"]),
    "quarterlyrating": ("QuarterlyRating", "SELF", ["id", "goalId", "employeeMailId", "projectId", "quarter", "starRating"]),
    "levelweightagepolicy": ("LevelWeightagePolicy", "OPEN", ["id", "appraisalYearId", "careerLevel", "deliveryPct", "deliveryChiefPct"]),
    # Module 11: Talent GPS, Skills & Upskilling
    "employeetalentgpsinfo": ("EmployeeTalentGPSInfo", "SELF", ["id", "employeeMailId", "currentProjectWorkStream", "primarySkill1"]),
    "talentdotoffamenomination": ("TalentDotOfFameNomination", "SELF", ["id", "talentGpsId", "nomineeMailId", "recognizedAt"]),
    "talentcertification": ("TalentCertification", "OPEN", ["id", "talentGpsId", "status", "name", "validUntil"]),
    "talentoption": ("TalentOption", "OPEN", ["id", "type", "label", "code", "active"]),
    "talentupskillingplan": ("TalentUpskillingPlan", "SELF", ["id", "employeeMailId", "appraisalYearId", "emAlignmentConfirmed"]),
    "talentupskillingtraining": ("TalentUpskillingTraining", "SELF", ["id", "employeeMailId", "appraisalYearId", "quarter", "skillCode", "trainingName"]),
    "talentfutureskill": ("TalentFutureSkill", "OPEN", ["id", "upskillingPlanId", "skillCode", "targetProficiency"]),
    "talentlegacyidea": ("TalentLegacyIdea", "SELF", ["id", "employeeMailId", "appraisalYearId", "category", "title", "description"]),
    # Module 12: Houseverse (Happiness Club) & Community
    "happinessmembership": ("HappinessMembership", "OPEN", ["id", "employeeId", "house", "pointsEarned"]),
    "happinessledgerentry": ("HappinessLedgerEntry", "OPEN", ["id", "house", "points", "category", "description"]),
    "happinesschiefevent": ("HappinessChiefEvent", "OPEN", ["id", "chiefOrder", "chiefArea", "title", "eventDate", "description"]),
    "happinessmediafolder": ("HappinessMediaFolder", "OPEN", ["id", "name"]),
    "happinessmedia": ("HappinessMedia", "OPEN", ["id", "folderId", "blobName", "fileName", "mimeType"]),
    "xablecommunity": ("XableCommunity", "OPEN", ["id", "slug", "name", "description", "category"]),
    "xablecommunitymember": ("XableCommunityMember", "OPEN", ["id", "communityId", "employeeId", "status", "role"]),
    "xableevent": ("XableEvent", "OPEN", ["id", "communityId", "title", "description", "startsAt", "endsAt"]),
    "xableannouncement": ("XableAnnouncement", "OPEN", ["id", "communityId", "title", "content", "category"]),
    "xablepost": ("XablePost", "OPEN", ["id", "communityId", "kind", "title", "body"]),
    # Module 13: Operations & Audit
    "auditlog": ("AuditLog", "ADMIN_ONLY", ["id", "entityType", "entityId", "action", "actorEmail", "createdAt"]),
}


class StandardVerticalAccessHandler(BasePolicyHandler):
    """
    Standard declarative handler for vertical, self, and lookup tables across modules.
    """

    def can_handle(self, table_name: str) -> bool:
        """Check if table is in standard registry."""
        return table_name.strip().lower() in _TABLE_REGISTRY

    def resolve_table_permission(
        self,
        table_name: str,
        user_context: UserContext,
        parameters: dict[str, Any],
    ) -> TablePermission:
        """Resolve permissions for standard vertical tables."""
        clean_table = table_name.strip().lower()
        canonical_name, filter_type, cols = _TABLE_REGISTRY[clean_table]

        # Bind parameters
        normalized_email = user_context.email.strip().lower()
        parameters["auth_user_email"] = normalized_email
        auth_verticals = [v.strip().upper() for v in user_context.access_scope.vertical_codes]
        parameters["auth_vertical_codes"] = auth_verticals

        # 1. Admin or EP always has full access
        if user_context.is_ca_admin or user_context.has_role(Role.EP):
            return self._build_open_permission(canonical_name, cols, AccessScope.ALL)

        # 2. Administrative-only tables (AuditLog, users, RoleAssignment)
        if filter_type == "ADMIN_ONLY":
            return TablePermission(
                table_name=canonical_name,
                can_read=False,
                scope=AccessScope.NONE,
                columns={},
                predicates=[PredicateSpec.deny()],
            )

        # 3. Open reference lookup tables
        if filter_type == "OPEN":
            return self._build_open_permission(canonical_name, cols, AccessScope.ALL)

        # 4. Vertical-scoped tables
        if filter_type == "VERTICAL":
            if auth_verticals:
                predicate = PredicateSpec.for_vertical(
                    column="verticalCode",
                    parameter_name="auth_vertical_codes",
                )
                return self._build_open_permission(
                    canonical_name, cols, AccessScope.VERTICAL, [predicate]
                )
            else:
                return TablePermission(
                    table_name=canonical_name,
                    can_read=False,
                    scope=AccessScope.NONE,
                    columns={},
                    predicates=[PredicateSpec.deny()],
                )

        # 5. Self-scoped tables
        if filter_type == "SELF":
            predicate = PredicateSpec.for_self(
                column="employeeMailId",
                parameter_name="auth_user_email",
            )
            return self._build_open_permission(
                canonical_name, cols, AccessScope.SELF, [predicate]
            )

        # Fallback default deny
        return TablePermission(
            table_name=canonical_name,
            can_read=False,
            scope=AccessScope.NONE,
            columns={},
            predicates=[PredicateSpec.deny()],
        )

    def _build_open_permission(
        self,
        canonical_name: str,
        cols: list[str],
        scope: AccessScope,
        predicates: list[PredicateSpec] | None = None,
    ) -> TablePermission:
        """Construct TablePermission for authorized table."""
        col_perms = {
            c.lower(): self._col(
                name=c,
                sensitivity=ColumnSensitivity.INTERNAL,
                can_select=True,
                can_filter=True,
                can_join=True,
                can_group=True,
                can_aggregate=True,
            )
            for c in cols
        }
        return TablePermission(
            table_name=canonical_name,
            can_read=True,
            scope=scope,
            columns=col_perms,
            predicates=predicates or [],
        )
