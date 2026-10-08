from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    groq_api_key: str
    gemini_api_key: str
    app_env: str = "development"
    secret_key: str = "change-this-in-production"
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
