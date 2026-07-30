from pydantic import BaseModel


class AssetResponse(BaseModel):
    id: int
    hostname: str
    ip_address: str
    operating_system: str
    asset_type: str
    owner: str
    status: str
    risk_level: str
    last_scan: str

    class Config:
        from_attributes = True