from enum import Enum

import reflex as rx
from reflex import constants


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


config = rx.Config(
    app_name="app",
    loglevel=LogLevel.DEBUG,
    env=rx.Env.DEV,
    frontend_port=80,
    state_manager_mode=constants.StateManagerMode.MEMORY,
    # env=rx.Env.PROD,
    # backend_host="152.42.211.214",
    # api_url="http://152.42.211.214:8000",
    # deploy_url="https://demo.thana.team",
)