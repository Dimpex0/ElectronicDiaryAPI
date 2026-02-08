from fastapi import BackgroundTasks

from audit.models import AuditLog
from database import SessionLocal


def write_log_to_db(user_id: int, action: str):
    db = SessionLocal()
    try:
        log_entry = AuditLog(user_id=user_id, action=action)
        db.add(log_entry)
        db.commit()
    except Exception as e:
        print(f"Failed to audit log: {e}")
    finally:
        db.close()

def log(tasks: BackgroundTasks, user_id: int, action: str):
    tasks.add_task(write_log_to_db, user_id=user_id, action=action)