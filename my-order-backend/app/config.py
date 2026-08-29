from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    jwt_issuer: str = "my-order-api"
    jwt_audience: str = "my-order-clients"
    environment: str = "development"
    allowed_origins: str = ""
    allowed_hosts: str = ""
    max_request_body_bytes: int = 1_048_576
    delivery_base_fee_mmk: float = 3500
    quote_expire_minutes: int = 30
    wallet_alert_threshold: float = 100000  # MMK; Admin gets flagged above this (PRD 5.6)
    refund_cap_mmk: float = 100000  # PRD 5.4: max refund per order, business to confirm
    dispute_window_hours: int = 48  # PRD 5.5

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("jwt_algorithm")
    @classmethod
    def only_allow_symmetric_algorithm(cls, value: str) -> str:
        if value != "HS256":
            raise ValueError("jwt_algorithm must be HS256")
        return value

    def csv(self, value: str) -> list[str]:
        return [item.strip() for item in value.split(",") if item.strip()]

    @model_validator(mode="after")
    def require_production_host_allowlist(self):
        if self.environment.lower() == "production" and not self.csv(self.allowed_hosts):
            raise ValueError("allowed_hosts must be configured in production")
        return self

settings = Settings()
