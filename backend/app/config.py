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

    rewriter_cost_per_word: int = 5
    rewriter_min_credits: int = 5000

    # Output caps to keep API spend bounded per request
    coach_max_tokens: int = 1800
    rewriter_analysis_max_tokens: int = 700
    rewriter_rewrite_max_tokens: int = 2800
    rewriter_repair_max_tokens: int = 2800

    # Models
    coach_model: str = "gpt-4o"
    advanced_coach_model: str = "gpt-4o"

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/esl_coach",
        alias="DATABASE_URL",
    )
    database_ssl_verify: bool = Field(default=True, alias="DATABASE_SSL_VERIFY")
    database_schema_bootstrap: bool = Field(default=False, alias="DATABASE_SCHEMA_BOOTSTRAP")
    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_jwt_secret: str = Field(default="", alias="SUPABASE_JWT_SECRET")
    jwt_secret_key: str = Field(default="local-dev-secret", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=60 * 24, alias="JWT_EXPIRE_MINUTES")

    demo_login_enabled: bool = Field(default=False, alias="DEMO_LOGIN_ENABLED")
    demo_login_email: str = Field(default="demo@student.test", alias="DEMO_LOGIN_EMAIL")
    demo_login_password: str = Field(default="demo1234", alias="DEMO_LOGIN_PASSWORD")
    demo_login_user_id: str = Field(default="demo-plus", alias="DEMO_LOGIN_USER_ID")

    # Polar payment integration
    polar_api_base_url: str = Field(default="https://api.polar.sh", alias="POLAR_API_BASE_URL")
    polar_access_token: str = Field(default="", alias="POLAR_ACCESS_TOKEN")
    polar_webhook_secret: str = Field(default="", alias="POLAR_WEBHOOK_SECRET")
    polar_product_id_starter: str = Field(default="", alias="POLAR_PRODUCT_ID_STARTER")
    polar_product_id_student_plus: str = Field(default="", alias="POLAR_PRODUCT_ID_STUDENT_PLUS")
    polar_product_id_pro: str = Field(default="", alias="POLAR_PRODUCT_ID_PRO")
    polar_product_id_credit_s: str = Field(default="", alias="POLAR_PRODUCT_ID_CREDIT_S")
    polar_product_id_credit_m: str = Field(default="", alias="POLAR_PRODUCT_ID_CREDIT_M")
    polar_product_id_credit_l: str = Field(default="", alias="POLAR_PRODUCT_ID_CREDIT_L")


@lru_cache
def get_settings() -> Settings:
    return Settings()
