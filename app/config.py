import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "development-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://plant_user:plant_password@localhost:5432/plant_app",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

