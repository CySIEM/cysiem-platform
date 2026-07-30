from database.database import SessionLocal
from database.models import Alert, Asset


class Team1Service:

    def get_dashboard_stats(self):
        db = SessionLocal()

        try:
            critical = db.query(Alert).filter(Alert.severity == "Critical").count()
            high = db.query(Alert).filter(Alert.severity == "High").count()
            medium = db.query(Alert).filter(Alert.severity == "Medium").count()
            assets = db.query(Asset).count()

            return {
                "critical": critical,
                "high": high,
                "medium": medium,
                "assets": assets
            }

        finally:
            db.close()

    def get_alerts(self):
        db = SessionLocal()

        try:
            alerts = db.query(Alert).all()

            return [
                {
                    "id": alert.id,
                    "severity": alert.severity,
                    "title": alert.title,
                    "source": alert.source,
                    "status": alert.status
                }
                for alert in alerts
            ]

        finally:
            db.close()