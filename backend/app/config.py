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
    basic_coaching_min_credits: int = 500
    deep_coaching_min_credits: int = 1200
    full_review_min_credits: int = 3000

    # Monthly credits per plan
    starter_monthly_credits: int = 20000
    student_plus_monthly_credits: int = 60000
    pro_monthly_credits: int = 150000

    humanize_cost_per_word: int = 5
    humanize_min_credits: int = 5000

    # Output caps to keep API spend bounded per request
    coach_max_tokens: int = 1800
    humanize_analysis_max_tokens: int = 700
    humanize_rewrite_max_tokens: int = 2800
    humanize_repair_max_tokens: int = 2800

    # Models
    coach_model: str = "gpt-4o"
    advanced_coach_model: str = "gpt-4o"

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/esl_coach",
        alias="DATABASE_URL",
    )
    supabase_jwt_secret: str = Field(default="", alias="SUPABASE_JWT_SECRET")


@lru_cache
def get_settings() -> Settings:
    return Settings()
