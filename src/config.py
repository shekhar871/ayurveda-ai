from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    # lite = file store | docker = Postgres+Qdrant+Neo4j | auto = try docker then lite
    app_mode: str = "docker"
    embedding_dim: int = 384
    api_secret_key: str = "dev-secret-change-in-prod"
    rate_limit_per_minute: int = 60

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "veda_master"
    postgres_user: str = "veda"
    postgres_password: str = "local_dev_secret"

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "veda_verses"

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "neo4j_local_secret"

    redis_url: str = "redis://localhost:6379/0"

    tei_url: str = "http://localhost:8080"
    vllm_url: str = "http://localhost:8001/v1"
    vllm_model: str = "meta-llama/Meta-Llama-3-8B-Instruct"
    embedding_fallback: str = "sentence-transformers"

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def qdrant_url(self) -> str:
        return f"http://{self.qdrant_host}:{self.qdrant_port}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
