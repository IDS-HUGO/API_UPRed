from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database MySQL
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "upred_db"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 días
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True
    
    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
