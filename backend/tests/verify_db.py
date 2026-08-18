import sys
from sqlalchemy import text
from app.core.config import settings
from app.database.base import Base
from app.database.session import engine, SessionLocal
from app.models.scheme import Scheme, EligibilityRule
from app.services.scheme_service import seed_schemes_if_empty


def verify_neon_connection():
    # 1. Verify DATABASE_URL is present
    has_db_url = bool(settings.DATABASE_URL and len(settings.DATABASE_URL.strip()) > 0)
    print(f"DATABASE_URL Loaded: {'YES' if has_db_url else 'NO'}")
    
    if not has_db_url or engine is None or SessionLocal is None:
        print("Connection Status: Failed (DATABASE_URL not configured)")
        print("PostgreSQL Reachable: NO")
        print("Tables Accessible: NO")
        print("Number of Schemes Retrieved: 0")
        return False

    try:
        # 2. Test raw connection and ping PostgreSQL
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            if result == 1:
                print("Connection Status: Successful")
                print("PostgreSQL Reachable: YES")
            else:
                print("Connection Status: Failed (Unexpected response)")
                print("PostgreSQL Reachable: NO")
                return False

        # 3. Create tables if they do not exist
        Base.metadata.create_all(bind=engine)
        
        # 4. Open session, seed if empty, and test query
        db = SessionLocal()
        try:
            # Seed schemes if empty
            seed_schemes_if_empty(db)
            
            # Query schemes
            schemes = db.query(Scheme).all()
            print("Tables Accessible: YES")
            print(f"Number of Schemes Retrieved: {len(schemes)}")
            
            # Verify rules can be accessed through relationship
            rule_count = db.query(EligibilityRule).count()
            print(f"Number of Eligibility Rules Retrieved: {rule_count}")
            return True
        finally:
            db.close()

    except Exception as e:
        print("Connection Status: Failed")
        print("PostgreSQL Reachable: NO")
        print("Tables Accessible: NO")
        print("Number of Schemes Retrieved: 0")
        print(f"Error Type: {type(e).__name__}")
        return False


if __name__ == "__main__":
    success = verify_neon_connection()
    sys.exit(0 if success else 1)
