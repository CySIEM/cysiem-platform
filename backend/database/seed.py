from database.database import SessionLocal, engine
from database.models import Base, Alert, Asset, Report, Investigation

# Create all tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# ------------------------
# Seed Alerts
# ------------------------
if db.query(Alert).count() == 0:
    alerts = [
        Alert(
            severity="Critical",
            title="SQL Injection",
            source="Web Server",
            status="Open"
        ),
        Alert(
            severity="High",
            title="Malware Detected",
            source="Endpoint",
            status="Investigating"
        ),
        Alert(
            severity="Medium",
            title="Failed Login Attempts",
            source="Firewall",
            status="Closed"
        )
    ]

    db.add_all(alerts)


# ------------------------
# Seed Assets
# ------------------------
if db.query(Asset).count() == 0:
    assets = [
        Asset(
            hostname="WEB-SERVER-01",
            ip_address="192.168.1.10",
            operating_system="Ubuntu 22.04",
            asset_type="Web Server",
            owner="IT Department",
            status="Healthy",
            risk_level="Low",
            last_scan="2026-07-29 09:30 AM"
        ),
        Asset(
            hostname="DB-SERVER-01",
            ip_address="192.168.1.20",
            operating_system="Windows Server 2022",
            asset_type="Database Server",
            owner="Database Team",
            status="Critical",
            risk_level="High",
            last_scan="2026-07-29 10:15 AM"
        ),
        Asset(
            hostname="CLIENT-PC-07",
            ip_address="192.168.1.35",
            operating_system="Windows 11",
            asset_type="Workstation",
            owner="Finance Department",
            status="Warning",
            risk_level="Medium",
            last_scan="2026-07-29 11:00 AM"
        )
    ]

    db.add_all(assets)


# ------------------------
# Seed Reports
# ------------------------
if db.query(Report).count() == 0:
    reports = [
        Report(
            name="Weekly Security Report",
            report_type="Weekly",
            generated_on="2026-07-30",
            status="Completed"
        ),
        Report(
            name="Monthly Incident Report",
            report_type="Monthly",
            generated_on="2026-07-28",
            status="Completed"
        )
    ]

    db.add_all(reports)


# ------------------------
# Seed Investigations
# ------------------------
if db.query(Investigation).count() == 0:
    investigations = [
        Investigation(
            case_id="CASE-1001",
            title="SQL Injection Attack",
            severity="Critical",
            status="Open",
            assigned_to="SOC Analyst"
        ),
        Investigation(
            case_id="CASE-1002",
            title="Ransomware Detection",
            severity="High",
            status="Investigating",
            assigned_to="Incident Response Team"
        ),
        Investigation(
            case_id="CASE-1003",
            title="Suspicious Login Activity",
            severity="Medium",
            status="Resolved",
            assigned_to="Security Team"
        )
    ]

    db.add_all(investigations)


# Commit all changes
db.commit()

db.close()

print("Database seeded successfully!")