from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import models  # noqa: F401,E402
from app.core.db import Base, engine, SessionLocal  # noqa: E402
from app.services.config_registry import get_registry  # noqa: E402
from app.services.workflow_service import WorkflowService  # noqa: E402
from app.services.security_service import SecurityService  # noqa: E402


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        WorkflowService(db, get_registry()).seed_definitions()
        SecurityService(db).seed_demo_users()
    finally:
        db.close()
    print('database initialized')


if __name__ == '__main__':
    main()
