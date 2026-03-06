from pydantic import BaseSettings, Field

class Settings(BaseSettings):
	# Database settings
	CONNECTION: str = Field(..., env='CONNECTION')
settings = Settings()
