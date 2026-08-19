import io
from datetime import date, timedelta
from PIL import Image, ImageDraw
from pypdf import PdfWriter

from app.services.kagazcheck.validation_service import validation_engine, Verhoeff
from app.services.kagazcheck.document_service import document_service
from app.services.kagazcheck.audit_service import scheme_audit_service
from app.services.kagazcheck.ocr_service import ocr_service


def _create_sample_pdf(text: str) -> bytes:
    """Helper to generate in-memory sample digital PDF with text stream."""
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    # Write text into PDF object stream
    buf = io.BytesIO()
    writer.write(buf)
    # Simple plain text wrapper for test mock
    return text.encode("utf-8")


def _create_sample_image(text: str = "", low_quality: bool = False) -> bytes:
    """Helper to generate in-memory sample image."""
    size = (50, 50) if low_quality else (800, 600)
    img = Image.new("RGB", size, color=(240, 240, 240) if not low_quality else (10, 10, 10))
    draw = ImageDraw.Draw(img)
    if not low_quality:
        draw.rectangle([50, 50, 750, 550], outline=(0, 100, 0), width=3)
        draw.text((70, 70), text or "Sample Govt Document Record", fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90 if not low_quality else 10)
    return buf.getvalue()


# Test 1: Verhoeff Checksum Algorithm
def test_verhoeff_checksum_algorithm():
    # Valid Aadhaar numbers with known valid Verhoeff checksums
    assert Verhoeff.validate("999941057058") is True
    assert Verhoeff.validate("367598324511") is True
    
    # Tampered / invalid checksums
    assert Verhoeff.validate("999941057059") is False  # Tampered last digit
    assert Verhoeff.validate("123456789012") is False


# Test 2: Valid Aadhaar Document Extraction and Validation
def test_valid_aadhaar_validation():
    # Valid Aadhaar with Verhoeff valid number
    text = (
        "GOVERNMENT OF INDIA\n"
        "UNIQUE IDENTIFICATION AUTHORITY OF INDIA\n"
        "Name: Satish Kumar\n"
        "DOB: 15/08/1982\n"
        "Gender: Male\n"
        "Address: Tumakuru, Karnataka 572101\n"
        "9999 4105 7058\n"
        "Mera Aadhaar, Meri Pehchan"
    )
    pdf_bytes = text.encode("utf-8")
    
    citizen_profile = {
        "name": "Satish Kumar",
        "state": "Karnataka",
        "age": 42,
    }
    
    res = document_service.analyze_document(
        file_bytes=pdf_bytes,
        file_name="Aadhaar_Card_Satish.pdf",
        mime_type="application/pdf",
        citizen_profile=citizen_profile,
        scheme_id="pm-kisan-001",
    )
    
    doc = res.document_result
    assert doc.document_type_code == "aadhaar"
    assert doc.is_detected is True
    assert doc.is_readable is True
    assert doc.overall_status == "VALID"
    assert doc.validity_status == "VALID"
    assert doc.citizen_details_match in ("MATCH", "PARTIAL_MATCH")
    assert doc.extracted_fields.get("id_number_masked") == "XXXX-XXXX-7058"
    assert doc.extracted_fields.get("holder_name") == "Satish Kumar"


# Test 3: Missing Required Fields in Document
def test_missing_required_fields():
    # Aadhaar file that has header but missing 12-digit number
    text = "GOVERNMENT OF INDIA\nUIDAI\nName: Ramesh Patel\nMera Aadhaar"
    pdf_bytes = text.encode("utf-8")
    
    res = document_service.analyze_document(
        file_bytes=pdf_bytes,
        file_name="Incomplete_Aadhaar.pdf",
        mime_type="application/pdf",
    )
    
    doc = res.document_result
    assert doc.overall_status == "INVALID"
    # Should flag missing Aadhaar number in fields_validation
    aadhaar_field = next((f for f in doc.fields_validation if f.field == "aadhaar_number"), None)
    assert aadhaar_field is not None
    assert aadhaar_field.is_valid is False


# Test 4: Missing Required Document in Scheme Readiness
def test_missing_required_documents_for_scheme():
    # Scheme PM-KISAN requires:
    # 1. Aadhaar Card
    # 2. Proof of Agricultural Land Ownership (ROR)
    # 3. Bank Account Passbook
    # 4. Mobile number linked
    
    # Analyze ONLY Aadhaar
    aadhaar_text = "UIDAI Aadhaar 9999 4105 7058 Name: Satish Kumar DOB: 15/08/1982"
    document_service.clear_session_documents()
    
    res = document_service.analyze_document(
        file_bytes=aadhaar_text.encode("utf-8"),
        file_name="Aadhaar.pdf",
        mime_type="application/pdf",
        scheme_id="pm-kisan-001",
    )
    
    audit = res.scheme_readiness
    assert audit is not None
    assert audit.scheme_id == "pm-kisan-001"
    assert audit.total_required_docs >= 4
    # With only Aadhaar + linked mobile, not all documents are ready
    assert audit.is_ready_to_apply is False
    assert audit.readiness_percentage < 100.0
    assert "Proof of Agricultural Land Ownership (ROR / Khasra / Khatauni)" in audit.critical_missing_docs or any("land" in s.lower() for s in audit.critical_missing_docs)


# Test 5: Invalid / Expired Document and Invalid Checksum
def test_invalid_and_expired_documents():
    # 1. Invalid Aadhaar checksum (first digit 0 or wrong Verhoeff)
    bad_aadhaar_text = "UIDAI Aadhaar 0123 4567 8901 Name: Test User"
    res1 = document_service.analyze_document(
        file_bytes=bad_aadhaar_text.encode("utf-8"),
        file_name="Bad_Aadhaar.pdf",
        mime_type="application/pdf",
    )
    assert res1.document_result.overall_status == "INVALID"
    assert res1.document_result.validity_status == "INVALID"

    # 2. Invalid Bank IFSC
    bad_bank_text = "Bank Passbook\nAccount No: 123456789012\nIFSC: INVALID_IFSC\nState Bank of India"
    res2 = document_service.analyze_document(
        file_bytes=bad_bank_text.encode("utf-8"),
        file_name="Bank_Passbook.pdf",
        mime_type="application/pdf",
    )
    assert res2.document_result.overall_status == "INVALID"

    # 3. Expired Income Certificate
    yesterday = (date.today() - timedelta(days=10)).strftime("%d/%m/%Y")
    expired_text = f"Income Certificate\nAnnual Income: ₹1,50,000\nValid Upto: {yesterday}\nTahsildar Seal"
    res3 = document_service.analyze_document(
        file_bytes=expired_text.encode("utf-8"),
        file_name="Income_Certificate.pdf",
        mime_type="application/pdf",
    )
    assert res3.document_result.overall_status == "INVALID"
    assert res3.document_result.validity_status == "EXPIRED"


# Test 6: Unreadable / Low Quality Image Assessment
def test_unreadable_insufficient_quality():
    # Very small 50x50 dark image
    low_q_bytes = _create_sample_image(low_quality=True)
    is_readable, score, metrics = ocr_service.assess_image_quality(low_q_bytes)
    
    assert score < 50.0
    assert is_readable is False or score <= 35.0


# Test 7: Multi-Document Dossier and 100% Overall Scheme Readiness
def test_multi_document_readiness():
    document_service.clear_session_documents()

    # 1. Upload Aadhaar
    doc1 = document_service.analyze_document(
        file_bytes="UIDAI Aadhaar 9999 4105 7058 Name: Satish Kumar DOB: 15/08/1982 Male Karnataka".encode("utf-8"),
        file_name="Aadhaar_Card.pdf",
        mime_type="application/pdf",
        scheme_id="pm-kisan-001",
    )
    assert doc1.document_result.overall_status == "VALID"

    # 2. Upload Land RoR
    doc2 = document_service.analyze_document(
        file_bytes="Government of Karnataka Bhoomi ROR Land Record\nSurvey No: 42/1A\nTotal Extent: 2.5 Acres\nHolder Name: Satish Kumar".encode("utf-8"),
        file_name="Land_Record_ROR.pdf",
        mime_type="application/pdf",
        scheme_id="pm-kisan-001",
    )
    assert doc2.document_result.overall_status == "VALID"

    # 3. Upload Bank Passbook
    doc3 = document_service.analyze_document(
        file_bytes="State Bank of India\nPassbook A/C No: 38920192831\nIFSC Code: SBIN0001234\nHolder: Satish Kumar".encode("utf-8"),
        file_name="Bank_Passbook.pdf",
        mime_type="application/pdf",
        scheme_id="pm-kisan-001",
    )
    assert doc3.document_result.overall_status == "VALID"

    # Now verify Scheme Readiness for PM-KISAN (all required docs uploaded)
    audit = doc3.scheme_readiness
    assert audit is not None
    assert audit.ready_docs_count == audit.total_required_docs
    assert audit.readiness_percentage == 100.0
    assert audit.is_ready_to_apply is True
    assert len(audit.critical_missing_docs) == 0


if __name__ == "__main__":
    test_verhoeff_checksum_algorithm()
    test_valid_aadhaar_validation()
    test_missing_required_fields()
    test_missing_required_documents_for_scheme()
    test_invalid_and_expired_documents()
    test_unreadable_insufficient_quality()
    test_multi_document_readiness()
    print("All KagazCheck deterministic validation tests passed successfully!")
