from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict, Field

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class ComplaintCreate(BaseModel):
    permanent_id: str = Field(min_length=2, max_length=80)
    institution_name: str = Field(min_length=2, max_length=255)
    region: str = ""
    complainant_name: str = Field(min_length=2, max_length=160)
    complainant_email: EmailStr
    category: str
    subject: str = Field(min_length=4, max_length=255)
    description: str = Field(min_length=10)
    document_url: str | None = None

class StatusUpdate(BaseModel):
    status: str
    comment: str = ""

class ComplaintOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    complaint_no: str
    category: str
    subject: str
    description: str
    assigned_cell: str
    status: str
    created_at: datetime
    updated_at: datetime
    due_at: datetime
    document_url: str | None
    institution: dict

class AuditOut(BaseModel):
    id: int
    action: str
    details: str
    timestamp: datetime
    user_name: str
    model_config = ConfigDict(from_attributes=True)
