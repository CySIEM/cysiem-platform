from database.database import SessionLocal
from database.models import Asset


class Team2Service:

    def get_assets(self):
        db = SessionLocal()

        try:
            assets = db.query(Asset).all()

            return [
                {
                    "id": asset.id,
                    "hostname": asset.hostname,
                    "ip_address": asset.ip_address,
                    "operating_system": asset.operating_system,
                    "asset_type": asset.asset_type,
                    "owner": asset.owner,
                    "status": asset.status,
                    "risk_level": asset.risk_level,
                    "last_scan": asset.last_scan
                }
                for asset in assets
            ]

        finally:
            db.close()