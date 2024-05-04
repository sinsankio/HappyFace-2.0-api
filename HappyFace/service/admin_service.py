from fastapi.encoders import jsonable_encoder

from entity.models import AuthAdmin, BasicRememberMe, Admin
from helper.database.mongodb.db_helper import DbHelper
from helper.hash.hash_helper import HashHelper


class AdminService:
    @staticmethod
    def authenticate(db_helper: DbHelper, admin: AuthAdmin) -> dict | None:
        if auth_admin := db_helper.find_one(
                {"username": admin.username, "password": admin.password}, {}
        ):
            return auth_admin

    @staticmethod
    def update(db_helper: DbHelper, admin: dict, new_admin: Admin, hashing: bool = True) -> dict:
        new_jsonable_admin = jsonable_encoder(new_admin)
        new_jsonable_admin["_id"] = admin["_id"]

        if hashing:
            new_jsonable_admin["username"] = HashHelper.hash(new_jsonable_admin["username"])
            new_jsonable_admin["password"] = HashHelper.hash(new_jsonable_admin["password"])
            new_jsonable_admin["authKey"] = HashHelper.hash(new_jsonable_admin["authKey"])
        else:
            new_jsonable_admin["username"] = admin["username"]
            new_jsonable_admin["password"] = admin["password"]

        if admin := db_helper.update_one({"_id": admin["_id"]}, new_jsonable_admin):
            return admin

    @staticmethod
    def remember_me(db_helper: DbHelper, remember_me: BasicRememberMe) -> dict | None:
        if admin := db_helper.find_one({"authKey": remember_me.auth_key}, {}):
            return admin
