import openai
import uvicorn
from dotenv import dotenv_values
from fastapi import FastAPI

from helper.crypto.aes.aes_crypto_helper import AesCryptoHelper
from helper.database.mongodb.db_helper import DbHelper
from helper.log.default.log_helper import LogHelper
from route.admin_router import router as admin_router
from route.organization_router import router as organization_router
from route.subject_router import router as subject_router
from route.utility_router import router as utility_router
from service.admin_service import AdminService
from service.auth_service import AuthService
from service.organization_service import OrganizationService
from service.subject_service import SubjectService

db_config = dotenv_values("config/database/mongodb.env")
log_config = dotenv_values("config/log/default.env")
crypto_config = dotenv_values("config/crypto/aes.env")
chat_config = dotenv_values("config/chat/openai.env")

app = FastAPI()


@app.on_event("startup")
def startup_client():
    app.db_helper = DbHelper()
    app.crypto_helper = AesCryptoHelper(crypto_config["KEY"])
    app.auth_service = AuthService()
    app.admin_service = AdminService()
    app.organization_service = OrganizationService()
    app.subject_service = SubjectService()
    openai.api_key = chat_config["API_KEY"]
    app.log_helper = LogHelper(
        logger_name=log_config["LOGGER_NAME"],
        log_file_name=log_config["LOG_FILE_NAME"],
        log_format_template=log_config["LOG_FORMAT_TEMPLATE"],
        log_file_open_mode=log_config["LOG_FILE_OPEN_MODE"]
    )
    app.db_helper.get_connected(
        db_uri=db_config["DB_URI"],
        db=db_config["DB_NAME"],
        log_helper=app.log_helper
    )
    app.log_helper.log_info_message("[Main] App initialized successfully")


@app.on_event("shutdown")
def shutdown_client():
    log_helper = app.log_helper
    db_helper = app.db_helper

    db_helper.get_disconnected(log_helper)
    log_helper.log_info_message("[Main] App disabled successfully")


if __name__ == "__main__":
    app.include_router(admin_router, tags=["admins"], prefix="/happyface/v1")
    app.include_router(organization_router, tags=["organizations"], prefix="/happyface/v1/orgs")
    app.include_router(subject_router, tags=["subjects"], prefix="/happyface/v1/orgs/subjects")
    app.include_router(utility_router, tags=["utils"], prefix="/happyface/v1/utils")

    uvicorn.run(app)
