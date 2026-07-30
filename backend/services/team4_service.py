from database.database import SessionLocal
from database.models import Report, Investigation


class Team4Service:

    def get_reports(self):
        db = SessionLocal()

        try:
            reports = db.query(Report).all()

            return [
                {
                    "id": report.id,
                    "name": report.name,
                    "report_type": report.report_type,
                    "generated_on": report.generated_on,
                    "status": report.status
                }
                for report in reports
            ]

        finally:
            db.close()

    def get_investigations(self):
        db = SessionLocal()

        try:
            investigations = db.query(Investigation).all()

            return [
                {
                    "id": investigation.id,
                    "case_id": investigation.case_id,
                    "title": investigation.title,
                    "severity": investigation.severity,
                    "status": investigation.status,
                    "assigned_to": investigation.assigned_to
                }
                for investigation in investigations
            ]

        finally:
            db.close()