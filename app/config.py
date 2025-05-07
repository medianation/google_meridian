from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    HOST: str
    PORT: int

    class Config:
        env_file_encoding = 'utf-8'
        env_file = '../.env'


settings = Settings()
