from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Graph RAG Fraud Platform"
    app_env: str = "dev"

    memgraph_uri: str = "bolt://memgraph:7687"
    memgraph_user: str = ""
    memgraph_password: str = ""

    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    qdrant_collection: str = "fraud_embeddings"
    qdrant_vector_size: int = 384

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    ollama_url: str = "http://ollama:11434"
    ollama_model: str = "mistral"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
