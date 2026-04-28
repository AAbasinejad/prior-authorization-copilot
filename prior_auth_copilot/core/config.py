from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Prior Auth Copilot"
    database_url: str = "sqlite:///./prior_auth.db"
    default_sla_hours: int = 24
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
