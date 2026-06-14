import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    chroma_dir: str = "./chroma_db"
    frontend_origin: str = "http://localhost:5173"

    base_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def data_dir(self) -> str:
        return os.path.join(self.base_dir, "data")

    @property
    def reference_proposals_dir(self) -> str:
        return os.path.join(self.data_dir, "reference_proposals")

    @property
    def guidelines_dir(self) -> str:
        return os.path.join(self.data_dir, "guidelines")

    @property
    def priority_areas_dir(self) -> str:
        return os.path.join(self.data_dir, "priority_areas")

    @property
    def ml_dataset_dir(self) -> str:
        return os.path.join(self.data_dir, "ml_dataset")

    @property
    def ml_model_path(self) -> str:
        return os.path.join(self.ml_dataset_dir, "approval_model.joblib")


@lru_cache()
def get_settings() -> Settings:
    return Settings()