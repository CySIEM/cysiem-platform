from sqlalchemy import Column, Integer, String
from database.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    severity = Column(String)
    title = Column(String)
    source = Column(String)
    status = Column(String)


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String)
    ip_address = Column(String)
    operating_system = Column(String)
    asset_type = Column(String)
    owner = Column(String)
    status = Column(String)
    risk_level = Column(String)
    last_scan = Column(String)


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    report_type = Column(String)
    generated_on = Column(String)
    status = Column(String)


class Investigation(Base):
    __tablename__ = "investigations"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String)
    title = Column(String)
    severity = Column(String)
    status = Column(String)
    assigned_to = Column(String)