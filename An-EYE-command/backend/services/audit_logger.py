from backend.models.audit_log_model import AuditLogModel


def log_action(db, incident_id, operator_id, action, notes=""):
    log = AuditLogModel(
        incident_id=incident_id,
        operator_id=operator_id,
        action=action,
        notes=notes,
    )

    db.add(log)
    db.commit()

    return log
