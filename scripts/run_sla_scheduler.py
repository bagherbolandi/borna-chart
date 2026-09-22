from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import models  # noqa: F401,E402
from app.core.db import SessionLocal  # noqa: E402
from app.services.config_registry import get_registry  # noqa: E402
from app.services.sla_service import SLAService  # noqa: E402


def main() -> None:
    db = SessionLocal()
    try:
        result = SLAService(db, get_registry()).run_scheduler()
    finally:
        db.close()
    print(
        {
            "scanned_instances": result.scanned_instances,
            "overdue_instances": result.overdue_instances,
            "escalated_instances": result.escalated_instances,
            "resolved_alerts": result.resolved_alerts,
            "created_alerts": result.created_alerts,
        }
    )


if __name__ == "__main__":
    main()
