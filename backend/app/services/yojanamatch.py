from typing import Any, List, Optional
from app.schemas.eligibility import (
    CitizenProfile,
    RuleEvaluationResult,
    SchemeMatchResult,
    EligibilityMatchResponse,
)
from app.data.verified_schemes import VERIFIED_SCHEMES_SEED


class YojanaMatchEngine:
    """
    Deterministic rule-based government scheme eligibility evaluation engine.
    Does NOT use LLMs for decision making; strictly evaluates factual eligibility criteria.
    """

    @staticmethod
    def _normalize_string(val: Any) -> str:
        if val is None:
            return ""
        return str(val).strip().lower()

    @classmethod
    def evaluate_rule(
        cls,
        field: str,
        operator: str,
        target_value_str: str,
        profile_dict: dict,
        description: Optional[str] = None,
    ) -> RuleEvaluationResult:
        actual_val = profile_dict.get(field)
        passed = False
        op = operator.strip().lower()

        try:
            if actual_val is None:
                # If profile lacks the required field, rule fails deterministically
                passed = False
            elif op == "equals":
                if isinstance(actual_val, bool):
                    target_bool = target_value_str.strip().lower() in ("true", "1", "yes")
                    passed = actual_val == target_bool
                elif isinstance(actual_val, (int, float)):
                    passed = float(actual_val) == float(target_value_str)
                else:
                    passed = cls._normalize_string(actual_val) == cls._normalize_string(target_value_str)

            elif op == "not_equals":
                if isinstance(actual_val, bool):
                    target_bool = target_value_str.strip().lower() in ("true", "1", "yes")
                    passed = actual_val != target_bool
                elif isinstance(actual_val, (int, float)):
                    passed = float(actual_val) != float(target_value_str)
                else:
                    passed = cls._normalize_string(actual_val) != cls._normalize_string(target_value_str)

            elif op in ("greater_than", "gt"):
                passed = float(actual_val) > float(target_value_str)

            elif op in ("greater_than_or_equal", "gte", "greater_than_or_equals"):
                passed = float(actual_val) >= float(target_value_str)

            elif op in ("less_than", "lt"):
                passed = float(actual_val) < float(target_value_str)

            elif op in ("less_than_or_equal", "lte", "less_than_or_equals"):
                passed = float(actual_val) <= float(target_value_str)

            elif op == "in":
                options = [cls._normalize_string(x) for x in target_value_str.split(",")]
                passed = cls._normalize_string(actual_val) in options

            elif op == "not_in":
                options = [cls._normalize_string(x) for x in target_value_str.split(",")]
                passed = cls._normalize_string(actual_val) not in options

            else:
                passed = False
        except (ValueError, TypeError):
            passed = False

        return RuleEvaluationResult(
            field=field,
            operator=operator,
            expected_value=target_value_str,
            actual_value=actual_val,
            passed=passed,
            description=description or f"Requires {field} {operator} {target_value_str}",
        )

    @classmethod
    def evaluate_scheme(
        cls,
        scheme_dict: dict,
        profile: CitizenProfile,
    ) -> SchemeMatchResult:
        profile_dict = profile.model_dump()
        rules = scheme_dict.get("rules", [])
        matched_rules: List[RuleEvaluationResult] = []
        failed_rules: List[RuleEvaluationResult] = []

        for r in rules:
            # Handle dictionary or ORM model instances
            field = r.field if hasattr(r, "field") else r["field"]
            operator = r.operator if hasattr(r, "operator") else r["operator"]
            value = r.value if hasattr(r, "value") else r["value"]
            description = r.description if hasattr(r, "description") else r.get("description")

            eval_res = cls.evaluate_rule(
                field=field,
                operator=operator,
                target_value_str=str(value),
                profile_dict=profile_dict,
                description=description,
            )
            if eval_res.passed:
                matched_rules.append(eval_res)
            else:
                failed_rules.append(eval_res)

        total_rules = len(rules)
        if total_rules == 0:
            score = 100.0
            eligible = True
        else:
            score = round((len(matched_rules) / total_rules) * 100.0, 1)
            eligible = len(failed_rules) == 0

        # Benefits & required docs handling
        benefits_raw = scheme_dict.get("benefits", [])
        if isinstance(benefits_raw, list):
            benefits = benefits_raw
        elif isinstance(benefits_raw, str):
            benefits = [benefits_raw]
        else:
            benefits = []

        docs_raw = scheme_dict.get("required_documents", [])
        if isinstance(docs_raw, list):
            required_docs = docs_raw
        elif isinstance(docs_raw, str):
            required_docs = [docs_raw]
        else:
            required_docs = []

        return SchemeMatchResult(
            scheme_id=str(scheme_dict.get("id", "")),
            scheme_name=scheme_dict.get("name", ""),
            short_description=scheme_dict.get("short_description"),
            detailed_description=scheme_dict.get("detailed_description"),
            match_score=score,
            eligible_status=eligible,
            matched_rules=matched_rules,
            failed_rules=failed_rules,
            benefits=benefits,
            required_documents=required_docs,
            official_source_url=scheme_dict.get("official_source_url", ""),
            application_url=scheme_dict.get("application_url"),
        )

    @classmethod
    def match_citizen(
        cls,
        profile: CitizenProfile,
        schemes: Optional[List[dict]] = None,
    ) -> EligibilityMatchResponse:
        active_schemes = schemes if schemes is not None else VERIFIED_SCHEMES_SEED
        results: List[SchemeMatchResult] = []

        for s in active_schemes:
            if s.get("active", True):
                result = cls.evaluate_scheme(s, profile)
                results.append(result)

        # Rank results: eligible (100%) first, then descending by score
        results.sort(key=lambda x: (x.eligible_status, x.match_score), reverse=True)

        eligible_count = sum(1 for r in results if r.eligible_status)

        return EligibilityMatchResponse(
            citizen_profile=profile,
            total_schemes_evaluated=len(results),
            eligible_schemes_count=eligible_count,
            results=results,
        )


yojanamatch_service = YojanaMatchEngine()
