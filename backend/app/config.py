from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ESL Academic Writing Coach"
    max_word_limit: int = 1200
    free_word_limit: int = 300

    # Credit costs per word by depth
    basic_coaching_cost_per_word: int = 1
    deep_coaching_cost_per_word: int = 2
    full_review_cost_per_word: int = 5

    # Monthly credits per plan
    starter_monthly_credits: int = 20000
    student_plus_monthly_credits: int = 60000
    pro_monthly_credits: int = 150000

    humanize_cost_per_word: int = 3

    # Models
    coach_model: str = "gpt-4o"
    advanced_coach_model: str = "gpt-4o"

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")


@lru_cache
def get_settings() -> Settings:
    return Settings()
