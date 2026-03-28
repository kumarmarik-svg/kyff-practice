import os
from datetime import timedelta
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()


def _build_db_url(
    user_var: str,
    password_var: str,
    host_var: str,
    port_var: str,
    name_var: str,
    fallback: str,
) -> str:
    user = os.environ.get(user_var)
    password = os.environ.get(password_var)
    host = os.environ.get(host_var)
    name = os.environ.get(name_var)
    if user and password and host and name:
        port = os.environ.get(port_var, "3306")
        return f"mysql+pymysql://{user}:{quote_plus(password)}@{host}:{port}/{name}"
    return os.environ.get("DATABASE_URL", fallback)


class BaseConfig:
    SECRET_KEY = os.environ["SECRET_KEY"]
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)

    RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = _build_db_url(
        "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME",
        "mysql+pymysql://root:password@localhost/kyff_dev",
    )


class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = _build_db_url(
        "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME",
        "",
    )


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = _build_db_url(
        "DB_USER", "DB_TEST_PASSWORD", "DB_HOST", "DB_PORT", "DB_TEST_NAME",
        "mysql+pymysql://root:password@localhost/kyff_test",
    )
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
