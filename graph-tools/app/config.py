from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    tenant_id: str = ""
    client_id: str = ""
    client_secret: str = ""
    graph_redirect_uri: str = "http://localhost:8000/auth/callback"
    graph_scopes: str = "User.Read Files.ReadWrite.All Notes.ReadWrite offline_access"

    graph_tools_api_key: str = ""
    token_encryption_key: str = ""
    data_dir: str = "/data"


settings = Settings()
