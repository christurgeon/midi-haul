from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: str | None = None
    database_url: str = "sqlite:///./data/midi_haul.db"
    midi_storage_dir: str = "./data/midi_files"
    scrape_rate_limit_delay: float = 1.5
    agent_schedule_cron: str = "0 2 * * *"
    agent_max_steps: int = 20
    crawler_max_depth: int = 3
    log_level: str = "INFO"
    brave_search_api_key: str | None = None
    agent_model: str = "claude-sonnet-4-5"


settings = Settings()
