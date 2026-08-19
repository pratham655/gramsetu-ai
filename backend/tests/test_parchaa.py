import io
import base64
import pytest
from pypdf import PdfReader
from fastapi import HTTPException

from app.schemas.parchaa import (
    ParchaaRequest,
    ParchaaCitizenProfile,
    ParchaaDocumentItem,
    DocumentStatusEnum,
)
from app.services.parchaa.parchaa_service import parchaa_service
from app.services.parchaa.data_service import (
    parchaa_data_service,
    mask_sensitive_id,
    sanitize_citizen_profile,
)
from app.services.parchaa.pdf_generator import pdf_generator


# Test 1: Parchaa Request Validation
def test_parchaa_request_validation():
    req = ParchaaRequest(
        scheme_id="pm-kisan-001",
        preferred_language="en",
    )
    assert req.scheme_id == "pm-kisan-001"
    assert req.preferred_language == "en"


# Test 2: Valid Scheme Retrieval
def test_valid_scheme_retrieval():
    scheme = parchaa_data_service.get_scheme_by_id("pm-kisan-001")
    assert scheme is not None
    assert scheme["name"] == "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)"
    assert scheme["category"] == "Agriculture"


# Test 3: Unknown Scheme Handling
def test_unknown_scheme_handling():
    req = ParchaaRequest(scheme_id="non-existent-scheme-999")
    with pytest.raises(HTTPException) as exc_info:
        parchaa_service.generate_parchaa(req)
    assert exc_info.value.status_code == 404
    assert "not found in verified" in exc_info.value.detail


# Test 4: Correct Scheme Summary Generation
def test_scheme_summary_generation():
    raw_scheme = parchaa_data_service.get_scheme_by_id("pm-kisan-001")
    summary = parchaa_data_service.assemble_scheme_summary(raw_scheme)
    assert summary.scheme_id == "pm-kisan-001"
    assert "₹6,000" in summary.detailed_description or "income support" in summary.short_description.lower()
    assert len(summary.main_benefits) > 0
    assert len(summary.eligibility_summary) > 0
    assert summary.official_source_url == "https://pmkisan.gov.in"


# Test 5: Required Document Extraction
def test_required_document_extraction():
    raw_scheme = parchaa_data_service.get_scheme_by_id("pm-kisan-001")
    docs = parchaa_data_service.assemble_document_items(raw_scheme)
    assert len(docs) >= 4
    doc_names = [d.document_name for d in docs]
    assert any("Aadhaar" in n for n in doc_names)
    assert any("Land" in n or "ROR" in n for n in doc_names)
    assert any("Passbook" in n or "Bank" in n for n in doc_names)


# Test 6: KagazCheck Readiness Integration
def test_kagazcheck_readiness_integration():
    raw_scheme = parchaa_data_service.get_scheme_by_id("pm-kisan-001")
    
    # Simulate KagazCheck audit results
    audit_readiness = [
        ParchaaDocumentItem(
            document_name="Aadhaar Card",
            status=DocumentStatusEnum.READY,
            enclosure_note="Verified UIDAI match",
        ),
        ParchaaDocumentItem(
            document_name="Bank Account Passbook",
            status=DocumentStatusEnum.NEEDS_ATTENTION,
            enclosure_note="IFSC mismatch warning",
        ),
    ]
    
    docs = parchaa_data_service.assemble_document_items(
        raw_scheme=raw_scheme,
        document_readiness=audit_readiness,
    )
    
    aadhaar_item = next(d for d in docs if "Aadhaar Card" in d.document_name)
    assert aadhaar_item.status == DocumentStatusEnum.READY
    assert aadhaar_item.enclosure_note == "Verified UIDAI match"
    
    bank_item = next(d for d in docs if "Bank" in d.document_name)
    assert bank_item.status == DocumentStatusEnum.NEEDS_ATTENTION


# Test 7: Citizen Profile Integration & YojanaMatch
def test_citizen_profile_integration():
    profile_data = {
        "name": "Basavaraj Gowda",
        "state": "Karnataka",
        "district": "Tumakuru",
        "occupation": "farmer",
        "age": 45,
        "landholding": 3.0,
        "bpl": True,
        "yojanamatch_eligible": True,
        "yojanamatch_score": 100.0,
    }
    sanitized = sanitize_citizen_profile(profile_data)
    assert sanitized is not None
    assert sanitized.name == "Basavaraj Gowda"
    assert sanitized.state == "Karnataka"
    assert sanitized.yojanamatch_eligible is True


# Test 8: Sensitive Data Masking
def test_sensitive_data_masking():
    # Aadhaar masking
    assert mask_sensitive_id("9999 4105 7058", "aadhaar") == "XXXX-XXXX-7058"
    assert mask_sensitive_id("9999-4105-7058", "aadhaar") == "XXXX-XXXX-7058"
    assert mask_sensitive_id("123456789012", "aadhaar") == "XXXX-XXXX-9012"
    
    # Bank account masking
    assert mask_sensitive_id("38920192831", "bank") == "XXXXXX2831"
    
    # Profile with raw PII sanitized
    profile_with_pii = {
        "name": "Ramesh Kumar",
        "aadhaar": "9999 4105 7058",
        "bank_account": "1234567890123",
    }
    sanitized = sanitize_citizen_profile(profile_with_pii)
    assert sanitized.aadhaar_masked == "XXXX-XXXX-7058"
    assert sanitized.bank_account_masked == "XXXXXX0123"


# Test 9: Missing Office Information Handling
def test_missing_office_information_handling():
    # Synthetic scheme without verified office metadata
    fake_scheme = {
        "id": "unverified-office-scheme",
        "name": "Test Unverified Scheme",
        "short_description": "A test scheme without office info",
        "detailed_description": "Detailed test scheme",
        "benefits": ["Benefit 1"],
        "required_documents": ["Aadhaar Card"],
        "state": "Karnataka",
        "official_source_url": "https://gov.in",
    }
    docs = parchaa_data_service.assemble_document_items(fake_scheme)
    app_info = parchaa_data_service.assemble_application_info(fake_scheme, docs)
    
    assert app_info.administrative_office.is_verified is False
    assert "not available in the current verified database" in app_info.administrative_office.unverified_notice


# Test 10: Missing Processing Timeline Handling
def test_missing_processing_timeline_handling():
    fake_scheme = {
        "id": "unverified-timeline-scheme",
        "name": "Test Unverified Scheme",
        "short_description": "A test scheme without timeline info",
        "detailed_description": "Detailed test scheme",
        "benefits": ["Benefit 1"],
        "required_documents": ["Aadhaar Card"],
        "official_source_url": "https://gov.in",
    }
    docs = parchaa_data_service.assemble_document_items(fake_scheme)
    app_info = parchaa_data_service.assemble_application_info(fake_scheme, docs)
    
    assert app_info.processing_timeline.is_verified is False
    assert "not available in the current verified database" in app_info.processing_timeline.unverified_notice


# Test 11: Official Portal Handling
def test_official_portal_handling():
    raw_scheme = parchaa_data_service.get_scheme_by_id("pm-kisan-001")
    docs = parchaa_data_service.assemble_document_items(raw_scheme)
    app_info = parchaa_data_service.assemble_application_info(raw_scheme, docs)
    assert app_info.official_portal_url == "https://pmkisan.gov.in/RegistrationFormNew.aspx"


# Test 12: PDF Generation
def test_pdf_generation():
    req = ParchaaRequest(
        scheme_id="pm-kisan-001",
        citizen_profile=ParchaaCitizenProfile(
            name="Ravi Kumar",
            state="Karnataka",
            district="Mandya",
            occupation="farmer",
            landholding=2.0,
            bpl=True,
            aadhaar_masked="XXXX-XXXX-7058",
            yojanamatch_eligible=True,
        ),
        document_readiness=[
            ParchaaDocumentItem(
                document_name="Aadhaar Card",
                status=DocumentStatusEnum.READY,
            ),
            ParchaaDocumentItem(
                document_name="Proof of Agricultural Land Ownership (ROR / Khasra / Khatauni)",
                status=DocumentStatusEnum.READY,
            ),
            ParchaaDocumentItem(
                document_name="Aadhaar-seeded Bank Account Passbook",
                status=DocumentStatusEnum.NEEDS_ATTENTION,
            ),
        ],
        preferred_language="en",
    )
    
    resp = parchaa_service.generate_parchaa(req)
    assert resp is not None
    assert resp.parchaa_id.startswith("parchaa_")
    assert resp.reference_number.startswith("GS-PARCHAA-")
    assert resp.pdf_base64 is not None
    assert len(resp.pdf_base64) > 1000


# Test 13: PDF is Valid & Readable
def test_pdf_validity_and_magic_bytes():
    req = ParchaaRequest(scheme_id="pm-kisan-001")
    pdf_bytes = parchaa_service.generate_parchaa_pdf_bytes(req)
    
    # PDF Magic Bytes check (%PDF-)
    assert pdf_bytes.startswith(b"%PDF-")
    
    # Check that pypdf can read the document
    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) >= 1
    page_text = reader.pages[0].extract_text()
    assert "GRAMSETU AI" in page_text
    assert "APPLICATION PARCHAA" in page_text
    assert "PM-KISAN" in page_text or "Pradhan Mantri" in page_text


# Test 14: Single-Page PDF Requirement
def test_single_page_pdf_requirement():
    # Test all 5 verified schemes to ensure they all render strictly to exactly 1 page
    scheme_ids = ["pm-kisan-001", "pmay-g-002", "pmmvy-003", "pm-jay-004", "raitha-vidya-005"]
    for s_id in scheme_ids:
        req = ParchaaRequest(
            scheme_id=s_id,
            citizen_profile=ParchaaCitizenProfile(
                name="Smt. Shanthamma",
                state="Karnataka",
                district="Tumakuru",
                occupation="farmer",
                landholding=2.5,
                bpl=True,
                aadhaar_masked="XXXX-XXXX-4511",
                yojanamatch_eligible=True,
            ),
        )
        pdf_bytes = parchaa_service.generate_parchaa_pdf_bytes(req)
        reader = PdfReader(io.BytesIO(pdf_bytes))
        assert len(reader.pages) == 1, f"Scheme {s_id} produced {len(reader.pages)} pages instead of exactly 1 page!"


# Test 15: No Fabricated Data Assertion
def test_no_fabricated_data():
    req = ParchaaRequest(scheme_id="pmay-g-002")
    resp = parchaa_service.generate_parchaa(req)
    # Ensure portal is real
    assert "awaassoft.nic.in" in resp.application_info.official_portal_url or "pmayg.nic.in" in resp.scheme.official_source_url
    # Ensure benefits are from verified seed
    assert any("₹1,20,000" in b for b in resp.scheme.main_benefits)


# Test 16: Multi-Language Request Handling
def test_multi_language_request_handling():
    for lang in ["en", "hi", "kn"]:
        req = ParchaaRequest(scheme_id="pm-kisan-001", preferred_language=lang)
        resp = parchaa_service.generate_parchaa(req)
        assert resp.language == lang
        assert resp.pdf_base64 is not None


# Test 17: Error Handling & Edge Cases
def test_preview_endpoint_helper():
    preview = parchaa_service.get_parchaa_preview(
        scheme_id="raitha-vidya-005",
        citizen_profile_dict={"name": "Kiran", "state": "Karnataka", "occupation": "farmer"},
        language="kn",
    )
    assert preview.scheme.scheme_id == "raitha-vidya-005"
    assert preview.citizen.name == "Kiran"
    assert preview.citizen.state == "Karnataka"
    assert preview.language == "kn"


if __name__ == "__main__":
    test_parchaa_request_validation()
    test_valid_scheme_retrieval()
    test_unknown_scheme_handling()
    test_scheme_summary_generation()
    test_required_document_extraction()
    test_kagazcheck_readiness_integration()
    test_citizen_profile_integration()
    test_sensitive_data_masking()
    test_missing_office_information_handling()
    test_missing_processing_timeline_handling()
    test_official_portal_handling()
    test_pdf_generation()
    test_pdf_validity_and_magic_bytes()
    test_single_page_pdf_requirement()
    test_no_fabricated_data()
    test_multi_language_request_handling()
    test_preview_endpoint_helper()
    print("All 17 Parchaa Generator tests passed successfully!")
