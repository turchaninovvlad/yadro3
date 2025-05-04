from pydantic_settings import BaseSettings

class ConfigDataBase(BaseSettings):
    SQLITE_DB_PATH: str = "src/app.db"
    DB_ECHO_LOG: bool = False

    @property
    def database_url(self) -> str:
        return f"sqlite+aiosqlite:///{self.SQLITE_DB_PATH}"

settings_db = ConfigDataBase()