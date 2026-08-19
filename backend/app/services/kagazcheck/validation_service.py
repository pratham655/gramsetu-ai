import re
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple
from app.schemas.kagazcheck import (
    FieldValidationResult,
    ProfileMatchItem,
)
import logging

logger = logging.getLogger(__name__)


class Verhoeff:
    """
    Official Verhoeff algorithm implementation for Aadhaar number checksum verification.
    """
    # The multiplication table
    d = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
        [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
        [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
        [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
        [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
        [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
        [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
        [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
        [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
    ]

    # The permutation table
    p = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
        [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
        [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
        [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
        [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
        [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
        [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
    ]

    # The inverse table
    inv = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]

    @classmethod
    def validate(cls, num_str: str) -> bool:
        """
        Validates if string of digits has a valid Verhoeff checksum.
        """
        digits = [c for c in num_str if c.isdigit()]
        if not digits:
            return False
        c = 0
        for i, item in enumerate(reversed(digits)):
            c = cls.d[c][cls.p[i % 8][int(item)]]
        return c == 0


class DocumentValidationEngine:
    """
    Deterministic rule-based validation engine for Indian government records and certificates.
    """

    @staticmethod
    def _normalize(val: Any) -> str:
        if val is None:
            return ""
        return str(val).strip().lower()

    @classmethod
    def _fuzzy_name_match(cls, name_a: str, name_b: str) -> Tuple[bool, float]:
        """
        Calculates similarity between citizen profile name and document holder name.
        """
        if not name_a or not name_b:
            return False, 0.0
        
        na = cls._normalize(name_a)
        nb = cls._normalize(name_b)
        
        if na == nb:
            return True, 1.0
        
        tokens_a = set(re.findall(r"\w+", na))
        tokens_b = set(re.findall(r"\w+", nb))
        
        if not tokens_a or not tokens_b:
            return False, 0.0
            
        intersection = tokens_a.intersection(tokens_b)
        union = tokens_a.union(tokens_b)
        jaccard = len(intersection) / len(union)
        
        # Check if first or last name matches
        if len(intersection) >= 1 and (len(tokens_a) == 1 or len(tokens_b) == 1):
            return True, max(0.85, jaccard)
            
        is_match = jaccard >= 0.5
        return is_match, round(jaccard, 2)

    @classmethod
    def validate_fields(
        cls,
        doc_type: str,
        extracted_fields: Dict[str, Any],
        is_readable: bool,
    ) -> Tuple[List[FieldValidationResult], str]:
        """
        Evaluates deterministic field validation rules according to statutory requirements.
        Returns: (fields_validation_list, validity_status: 'VALID' | 'WARNING' | 'INVALID' | 'EXPIRED')
        """
        results: List[FieldValidationResult] = []
        is_all_valid = True
        has_warning = False
        is_expired = False

        if not is_readable:
            results.append(
                FieldValidationResult(
                    field="readability",
                    label="Document Legibility",
                    extracted_value="Low / Unreadable",
                    is_valid=False,
                    rule_description="Document must be legible, unblurred, and have sufficient contrast.",
                    issue_reason="Image resolution or contrast is too low to reliably extract statutory text.",
                )
            )
            return results, "INVALID"

        if doc_type == "aadhaar":
            # 1. Aadhaar Number & Verhoeff Checksum
            raw_uid = extracted_fields.get("aadhaar_number", "")
            masked_uid = extracted_fields.get("id_number_masked")
            
            if not raw_uid and not masked_uid:
                is_all_valid = False
                results.append(
                    FieldValidationResult(
                        field="aadhaar_number",
                        label="12-digit Aadhaar Number",
                        extracted_value=None,
                        is_valid=False,
                        rule_description="Must contain 12-digit UID issued by UIDAI.",
                        issue_reason="Aadhaar number was not detected in document.",
                    )
                )
            else:
                uid_clean = "".join(filter(str.isdigit, raw_uid or ""))
                if len(uid_clean) == 12:
                    # UIDAI standard: first digit cannot be 0 or 1
                    first_digit_valid = uid_clean[0] not in ("0", "1")
                    # Check Verhoeff checksum algorithm
                    checksum_valid = Verhoeff.validate(uid_clean)
                    
                    if first_digit_valid and checksum_valid:
                        results.append(
                            FieldValidationResult(
                                field="aadhaar_number",
                                label="12-digit Aadhaar Number",
                                extracted_value=masked_uid or f"XXXX-XXXX-{uid_clean[-4:]}",
                                is_valid=True,
                                rule_description="12-digit UID verified with statutory Verhoeff checksum.",
                            )
                        )
                    else:
                        is_all_valid = False
                        results.append(
                            FieldValidationResult(
                                field="aadhaar_number",
                                label="12-digit Aadhaar Number",
                                extracted_value=masked_uid or "Invalid Format",
                                is_valid=False,
                                rule_description="Must pass statutory Verhoeff checksum algorithm.",
                                issue_reason="Invalid Aadhaar number checksum or starting digit.",
                            )
                        )
                else:
                    # If partially masked or detected via masked pattern
                    results.append(
                        FieldValidationResult(
                            field="aadhaar_number",
                            label="Aadhaar Number (Masked)",
                            extracted_value=masked_uid or "Masked UID",
                            is_valid=True,
                            rule_description="Masked Aadhaar pattern recognized.",
                        )
                    )

            # 2. Holder Name
            name = extracted_fields.get("holder_name")
            if name:
                results.append(
                    FieldValidationResult(
                        field="holder_name",
                        label="Cardholder Name",
                        extracted_value=name,
                        is_valid=True,
                        rule_description="Cardholder name present on identity record.",
                    )
                )
            else:
                has_warning = True
                results.append(
                    FieldValidationResult(
                        field="holder_name",
                        label="Cardholder Name",
                        extracted_value=None,
                        is_valid=False,
                        rule_description="Cardholder name should be clearly visible.",
                        issue_reason="Name could not be unambiguously extracted.",
                    )
                )

            # 3. DOB / YOB
            dob = extracted_fields.get("dob")
            if dob:
                results.append(
                    FieldValidationResult(
                        field="dob",
                        label="Date / Year of Birth",
                        extracted_value=dob,
                        is_valid=True,
                        rule_description="Birth record or Year of Birth present.",
                    )
                )
            else:
                has_warning = True
                results.append(
                    FieldValidationResult(
                        field="dob",
                        label="Date / Year of Birth",
                        extracted_value=None,
                        is_valid=False,
                        rule_description="Birth date or year should be visible.",
                        issue_reason="DOB/YOB not clearly identified.",
                    )
                )

        elif doc_type == "land_record":
            # 1. Survey / Khata / Khasra Number
            survey = extracted_fields.get("survey_number")
            if survey:
                results.append(
                    FieldValidationResult(
                        field="survey_number",
                        label="Survey / Khasra / Khata No.",
                        extracted_value=survey,
                        is_valid=True,
                        rule_description="Must indicate official parcel survey number or Khatauni ID.",
                    )
                )
            else:
                is_all_valid = False
                results.append(
                    FieldValidationResult(
                        field="survey_number",
                        label="Survey / Khasra / Khata No.",
                        extracted_value=None,
                        is_valid=False,
                        rule_description="Must specify legal land parcel identifier.",
                        issue_reason="Survey/Khata number missing in document.",
                    )
                )

            # 2. Land Area / Extent
            area = extracted_fields.get("land_area_acres")
            if area is not None and area > 0:
                results.append(
                    FieldValidationResult(
                        field="land_area_acres",
                        label="Agricultural Land Extent",
                        extracted_value=f"{area} Acres ({extracted_fields.get('raw_extent_str', '')})",
                        is_valid=True,
                        rule_description="Must record cultivable land extent in standard units.",
                    )
                )
            else:
                has_warning = True
                results.append(
                    FieldValidationResult(
                        field="land_area_acres",
                        label="Agricultural Land Extent",
                        extracted_value=None,
                        is_valid=False,
                        rule_description="Land area extent should be documented.",
                        issue_reason="Extent area not clearly quantified in acres/guntas.",
                    )
                )

            # 3. Pattedar / Owner Name
            name = extracted_fields.get("holder_name")
            if name:
                results.append(
                    FieldValidationResult(
                        field="holder_name",
                        label="Pattedar / Land Owner",
                        extracted_value=name,
                        is_valid=True,
                        rule_description="Owner / Pattedar name recorded in revenue registry.",
                    )
                )

        elif doc_type == "bank_passbook":
            # 1. IFSC Code
            ifsc = extracted_fields.get("ifsc_code")
            if ifsc and re.match(r"^[A-Z]{4}0[A-Z0-9]{6}$", ifsc):
                results.append(
                    FieldValidationResult(
                        field="ifsc_code",
                        label="Bank IFSC Code",
                        extracted_value=ifsc,
                        is_valid=True,
                        rule_description="Valid 11-character RBI bank branch IFSC.",
                    )
                )
            else:
                is_all_valid = False
                results.append(
                    FieldValidationResult(
                        field="ifsc_code",
                        label="Bank IFSC Code",
                        extracted_value=ifsc or "Missing",
                        is_valid=False,
                        rule_description="Must have valid RBI IFSC format (e.g. SBIN0001234).",
                        issue_reason="Invalid or missing IFSC code.",
                    )
                )

            # 2. Account Number
            ac = extracted_fields.get("account_number")
            ac_masked = extracted_fields.get("account_masked")
            if ac or ac_masked:
                results.append(
                    FieldValidationResult(
                        field="account_number",
                        label="Bank Account Number",
                        extracted_value=ac_masked or "XXXXXX",
                        is_valid=True,
                        rule_description="Aadhaar-seedable operational bank account number.",
                    )
                )
            else:
                is_all_valid = False
                results.append(
                    FieldValidationResult(
                        field="account_number",
                        label="Bank Account Number",
                        extracted_value=None,
                        is_valid=False,
                        rule_description="Bank account number must be visible.",
                        issue_reason="Account number could not be extracted.",
                    )
                )

            # 3. Bank Name
            bank = extracted_fields.get("bank_name")
            if bank:
                results.append(
                    FieldValidationResult(
                        field="bank_name",
                        label="Bank Institution",
                        extracted_value=bank,
                        is_valid=True,
                        rule_description="Recognized Scheduled Commercial or Rural Regional Bank.",
                    )
                )

        elif doc_type == "ration_card":
            cat = extracted_fields.get("card_category")
            rc_no = extracted_fields.get("ration_card_number")
            if cat:
                results.append(
                    FieldValidationResult(
                        field="card_category",
                        label="Ration Entitlement Category",
                        extracted_value=cat,
                        is_valid=True,
                        rule_description="NFSA / State ration entitlement category (BPL/AAY/PHH/APL).",
                    )
                )
            if rc_no:
                results.append(
                    FieldValidationResult(
                        field="ration_card_number",
                        label="Ration Card / NFSA ID",
                        extracted_value=rc_no,
                        is_valid=True,
                        rule_description="Official food security ration card identifier.",
                    )
                )

        elif doc_type == "income_certificate":
            inc = extracted_fields.get("annual_income")
            if inc is not None and inc > 0:
                results.append(
                    FieldValidationResult(
                        field="annual_income",
                        label="Certified Annual Income",
                        extracted_value=f"₹{int(inc):,}",
                        is_valid=True,
                        rule_description="Certified annual household income figure.",
                    )
                )
            # Check expiry date if present
            exp = extracted_fields.get("expiry_date")
            if exp:
                try:
                    # parse dd/mm/yyyy or dd-mm-yyyy
                    clean_exp = exp.replace("-", "/")
                    exp_date = datetime.strptime(clean_exp, "%d/%m/%Y").date()
                    if exp_date < date.today():
                        is_expired = True
                        is_all_valid = False
                        results.append(
                            FieldValidationResult(
                                field="expiry_date",
                                label="Certificate Expiration",
                                extracted_value=f"Expired on {exp}",
                                is_valid=False,
                                rule_description="Certificate must be currently valid and unexpired.",
                                issue_reason=f"Income certificate expired on {exp}. Renewal required.",
                            )
                        )
                    else:
                        results.append(
                            FieldValidationResult(
                                field="expiry_date",
                                label="Certificate Expiration",
                                extracted_value=f"Valid till {exp}",
                                is_valid=True,
                                rule_description="Certificate is active and within statutory validity period.",
                            )
                        )
                except ValueError:
                    pass

        elif doc_type == "pan_card":
            pan = extracted_fields.get("pan_number")
            pan_masked = extracted_fields.get("id_number_masked")
            if pan and re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", pan):
                results.append(
                    FieldValidationResult(
                        field="pan_number",
                        label="Permanent Account Number (PAN)",
                        extracted_value=pan_masked or pan,
                        is_valid=True,
                        rule_description="Statutory 10-character alphanumeric PAN issued by Income Tax Dept.",
                    )
                )
            else:
                is_all_valid = False
                results.append(
                    FieldValidationResult(
                        field="pan_number",
                        label="PAN Card Number",
                        extracted_value=pan or "Invalid",
                        is_valid=False,
                        rule_description="Must follow 5-letters + 4-digits + 1-letter format.",
                        issue_reason="Invalid PAN number format.",
                    )
                )

        else:
            # General document
            results.append(
                FieldValidationResult(
                    field="general_document",
                    label="Document Record",
                    extracted_value=doc_type.replace("_", " ").title(),
                    is_valid=True,
                    rule_description="Uploaded record accepted for preliminary audit.",
                )
            )

        # Compute final validity status
        if is_expired:
            validity_status = "EXPIRED"
        elif not is_all_valid:
            validity_status = "INVALID"
        elif has_warning:
            validity_status = "WARNING"
        else:
            validity_status = "VALID"

        return results, validity_status

    @classmethod
    def cross_match_citizen_profile(
        cls,
        extracted_fields: Dict[str, Any],
        citizen_profile: Optional[Dict[str, Any]],
    ) -> Tuple[str, List[ProfileMatchItem]]:
        """
        Cross-matches extracted document attributes with the citizen's active profile.
        Returns: (match_status: 'MATCH' | 'PARTIAL_MATCH' | 'MISMATCH' | 'UNVERIFIED', match_items)
        """
        if not citizen_profile:
            return "UNVERIFIED", []

        items: List[ProfileMatchItem] = []
        matches_count = 0
        total_checks = 0

        # 1. Name Cross-Match
        prof_name = citizen_profile.get("name") or citizen_profile.get("full_name")
        doc_name = extracted_fields.get("holder_name")
        if prof_name and doc_name:
            total_checks += 1
            is_match, score = cls._fuzzy_name_match(prof_name, doc_name)
            if is_match:
                matches_count += 1
                items.append(
                    ProfileMatchItem(
                        field="name",
                        profile_value=prof_name,
                        document_value=doc_name,
                        matched=True,
                        confidence=score,
                        details=f"Name matches citizen profile ({int(score * 100)}% match)",
                    )
                )
            else:
                items.append(
                    ProfileMatchItem(
                        field="name",
                        profile_value=prof_name,
                        document_value=doc_name,
                        matched=False,
                        confidence=score,
                        details=f"Name discrepancy: profile '{prof_name}' vs document '{doc_name}'",
                    )
                )

        # 2. State Cross-Match
        prof_state = citizen_profile.get("state")
        doc_state = extracted_fields.get("state")
        if prof_state and doc_state:
            total_checks += 1
            if cls._normalize(prof_state) == cls._normalize(doc_state):
                matches_count += 1
                items.append(
                    ProfileMatchItem(
                        field="state",
                        profile_value=prof_state,
                        document_value=doc_state,
                        matched=True,
                        confidence=1.0,
                        details=f"Jurisdiction state matches: {prof_state}",
                    )
                )
            else:
                items.append(
                    ProfileMatchItem(
                        field="state",
                        profile_value=prof_state,
                        document_value=doc_state,
                        matched=False,
                        confidence=0.0,
                        details=f"State mismatch: profile is in '{prof_state}', document indicates '{doc_state}'",
                    )
                )

        # 3. Landholding Cross-Match
        prof_land = citizen_profile.get("landholding")
        doc_land = extracted_fields.get("land_area_acres")
        if prof_land is not None and doc_land is not None:
            total_checks += 1
            diff = abs(float(prof_land) - float(doc_land))
            if diff <= 0.5:
                matches_count += 1
                items.append(
                    ProfileMatchItem(
                        field="landholding",
                        profile_value=f"{prof_land} Acres",
                        document_value=f"{doc_land} Acres",
                        matched=True,
                        confidence=1.0,
                        details=f"Landholding extent confirmed: {doc_land} Acres (within tolerance)",
                    )
                )
            else:
                items.append(
                    ProfileMatchItem(
                        field="landholding",
                        profile_value=f"{prof_land} Acres",
                        document_value=f"{doc_land} Acres",
                        matched=False,
                        confidence=0.5,
                        details=f"Land extent variance: profile has {prof_land} Acres, RoR indicates {doc_land} Acres",
                    )
                )

        if total_checks == 0:
            return "UNVERIFIED", items
        elif matches_count == total_checks:
            return "MATCH", items
        elif matches_count > 0:
            return "PARTIAL_MATCH", items
        else:
            return "MISMATCH", items


validation_engine = DocumentValidationEngine()
