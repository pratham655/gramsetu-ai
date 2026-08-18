from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.scheme import Scheme, EligibilityRule
from app.data.verified_schemes import VERIFIED_SCHEMES_SEED
import logging

logger = logging.getLogger(__name__)


def seed_schemes_if_empty(db: Session) -> None:
    """
    Seeds verified schemes and their eligibility rules into PostgreSQL if the schemes table is empty.
    """
    try:
        count = db.query(Scheme).count()
        if count == 0:
            logger.info("Database schemes table is empty. Seeding verified schemes...")
            for s_data in VERIFIED_SCHEMES_SEED:
                scheme = Scheme(
                    id=s_data["id"],
                    name=s_data["name"],
                    short_description=s_data["short_description"],
                    detailed_description=s_data["detailed_description"],
                    benefits=s_data["benefits"],
                    state=s_data.get("state"),
                    category=s_data.get("category"),
                    occupation=s_data.get("occupation"),
                    official_source_url=s_data["official_source_url"],
                    application_url=s_data.get("application_url"),
                    required_documents=s_data["required_documents"],
                    active=s_data.get("active", True),
                )
                for r_data in s_data.get("rules", []):
                    rule = EligibilityRule(
                        scheme_id=scheme.id,
                        field=r_data["field"],
                        operator=r_data["operator"],
                        value=str(r_data["value"]),
                        description=r_data.get("description"),
                    )
                    scheme.rules.append(rule)
                db.add(scheme)
            db.commit()
            logger.info("Seeding completed successfully.")
    except Exception as e:
        logger.error(f"Error seeding schemes: {e}")
        db.rollback()


def get_active_schemes(db: Optional[Session] = None) -> List[dict]:
    """
    Retrieves active schemes from PostgreSQL if available, or returns verified seed dataset.
    """
    if db is not None:
        try:
            schemes = db.query(Scheme).filter(Scheme.active == True).all()
            if schemes:
                result = []
                for s in schemes:
                    result.append({
                        "id": s.id,
                        "name": s.name,
                        "short_description": s.short_description,
                        "detailed_description": s.detailed_description,
                        "benefits": s.benefits,
                        "state": s.state,
                        "category": s.category,
                        "occupation": s.occupation,
                        "official_source_url": s.official_source_url,
                        "application_url": s.application_url,
                        "required_documents": s.required_documents,
                        "active": s.active,
                        "rules": [
                            {
                                "id": r.id,
                                "field": r.field,
                                "operator": r.operator,
                                "value": r.value,
                                "description": r.description,
                            }
                            for r in s.rules
                        ],
                    })
                return result
        except Exception as e:
            logger.warning(f"Unable to query PostgreSQL schemes, using verified seed data: {e}")

    return VERIFIED_SCHEMES_SEED
