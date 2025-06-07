from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from typing import Optional

Base = declarative_base()

# Database models
class Profile(Base):
    __tablename__ = "profiles"
    id = Column(String, primary_key=True)
    type = Column(String)  # "mac" or "tpm"
    user_data = Column(String)
    meta_data = Column(String)
    api_token = Column(String, nullable=True)

class Pending(Base):
    __tablename__ = "pending"
    id = Column(String, primary_key=True)
    data = Column(String)

# Pydantic request models
class AttestationData(BaseModel):
    quote: str
    nonce: str
    aik_pub: str
    expected_hash: str

class BootstrapRequest(BaseModel):
    serial_number: str
    bios_vendor: Optional[str]
    bios_version: Optional[str]
    tpm: Optional[AttestationData]
    api_token: Optional[str] = None

class UserData(BaseModel):
    hostname: str
    ssh_authorized_keys: Optional[list[str]] = []
    packages: Optional[list[str]] = []
    runcmd: Optional[list[str]] = []

class MetaData(BaseModel):
    instance_id: str
    local_hostname: str