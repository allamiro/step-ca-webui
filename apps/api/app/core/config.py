from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "PKI API"
    api_prefix: str = "/api"

    database_url: str = "postgresql+psycopg2://pki:pki@postgres:5432/pki"
    redis_url: str = "redis://redis:6379/0"

    keycloak_issuer: str = "http://keycloak:8080/realms/pki"
    keycloak_jwks_url: str = "http://keycloak:8080/realms/pki/protocol/openid-connect/certs"
    keycloak_audience: str = "pki-api"

    step_ca_url: str = "https://step-ca:9000"
    step_ca_fingerprint: str = ""
    scim_bearer_token: str = "dev-scim-token"


settings = Settings()
