from pydantic import BaseModel, Field, field_validator


class IssueCertificateRequest(BaseModel):
    common_name: str = Field(min_length=1, max_length=255)
    sans: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("common_name")
    @classmethod
    def validate_cn(cls, value: str) -> str:
        if any(ch in value for ch in (";", "|", "&", "$", "`")):
            raise ValueError("Invalid character in common_name")
        return value.strip()


class RenewCertificateRequest(BaseModel):
    certificate_id: int


class RevokeCertificateRequest(BaseModel):
    certificate_id: int
    reason: str = Field(default="unspecified", max_length=255)


class CertificateOut(BaseModel):
    id: int
    common_name: str
    sans: str
    status: str

    class Config:
        from_attributes = True
