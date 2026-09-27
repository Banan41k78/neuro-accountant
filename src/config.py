from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # HF
    hf_token: str = ""
    base_model: str = "Qwen/Qwen2.5-7B-Instruct"
    embed_model: str = "intfloat/multilingual-e5-large"
    adapter_path: str = "./models/lora-adapter"

    # LLM через OpenAI-совместимый API
    openai_api_key: str = ""
    openai_base_url: str = "https://api.aitunnel.ru/v1/"
    openai_model: str = "gpt-4.1-nano"

    # Хранилище
    chroma_path: str = "./chroma_db"
    common_collection: str = "common"
    contour_collection: str = "contour_romashka"

    # Данные
    common_data_path: str = "./data/common"
    contour_data_path: str = "./data/contour/romashka"


settings = Settings()