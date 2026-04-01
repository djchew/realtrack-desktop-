from datetime import date, datetime


def serialize(obj) -> dict:
    """Convert a SQLAlchemy model instance to a JSON-serialisable dict."""
    d = {}
    for column in obj.__table__.columns:
        val = getattr(obj, column.name)
        if isinstance(val, (date, datetime)):
            d[column.name] = val.isoformat()
        else:
            d[column.name] = val
    return d
