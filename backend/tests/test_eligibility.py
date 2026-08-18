from app.schemas.eligibility import CitizenProfile
from app.services.yojanamatch import yojanamatch_service


def test_yojanamatch_farmer_profile():
    profile = CitizenProfile(
        age=42,
        income=180000,
        state="Karnataka",
        district="Tumakuru",
        gender="male",
        occupation="farmer",
        landholding=2.5,
        category="OBC",
        bpl=True,
    )
    response = yojanamatch_service.match_citizen(profile)
    
    assert response.total_schemes_evaluated >= 4
    assert response.eligible_schemes_count >= 3
    
    # PM-KISAN should be eligible
    pm_kisan = next((s for s in response.results if s.scheme_id == "pm-kisan-001"), None)
    assert pm_kisan is not None
    assert pm_kisan.eligible_status is True
    assert pm_kisan.match_score == 100.0
    assert len(pm_kisan.failed_rules) == 0

    # PMMVY should fail on gender
    pmmvy = next((s for s in response.results if s.scheme_id == "pmmvy-003"), None)
    assert pmmvy is not None
    assert pmmvy.eligible_status is False
    assert any(r.field == "gender" and not r.passed for r in pmmvy.failed_rules)


def test_yojanamatch_female_pregnant_mother():
    profile = CitizenProfile(
        age=24,
        income=250000,
        state="Uttar Pradesh",
        gender="female",
        occupation="homemaker",
        bpl=False,
    )
    response = yojanamatch_service.match_citizen(profile)
    pmmvy = next((s for s in response.results if s.scheme_id == "pmmvy-003"), None)
    assert pmmvy is not None
    assert pmmvy.eligible_status is True
    assert pmmvy.match_score == 100.0


def test_yojanamatch_state_filtering():
    profile = CitizenProfile(
        state="Maharashtra",
        occupation="farmer",
        landholding=3.0,
    )
    response = yojanamatch_service.match_citizen(profile)
    # Karnataka Raitha Vidya Nidhi should fail because state is Maharashtra
    raitha = next((s for s in response.results if s.scheme_id == "raitha-vidya-005"), None)
    assert raitha is not None
    assert raitha.eligible_status is False
    assert any(r.field == "state" and not r.passed for r in raitha.failed_rules)


if __name__ == "__main__":
    test_yojanamatch_farmer_profile()
    test_yojanamatch_female_pregnant_mother()
    test_yojanamatch_state_filtering()
    print("All YojanaMatch service tests passed successfully!")
