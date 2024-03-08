from typing import Any

import pymongo
from pymongo import MongoClient

from helper.database.abstract_db_helper import AbstractDbHelper
from helper.log.default.log_helper import LogHelper


class DbHelper(AbstractDbHelper):
    def __init__(self) -> None:
        self.__mongo_client = None
        self.__database = None

    @property
    def mongo_client(self) -> MongoClient:
        return self.__mongo_client

    @mongo_client.setter
    def mongo_client(self, mongo_client: MongoClient):
        self.__mongo_client = mongo_client

    @property
    def database(self):
        return self.__database

    @database.setter
    def database(self, database):
        self.__database = database

    def get_connected(self, db_uri: str, db: str, log_helper: LogHelper):
        self.mongo_client = MongoClient(db_uri)
        self.database = self.mongo_client[db]

        log_helper.log_info_message(f"[DbHelper] Connected with the MongoDB: {self.database} successfully")
        return self

    def get_disconnected(self, log_helper: LogHelper):
        self.mongo_client.close()

        log_helper.log_info_message(f"[DbHelper] Disconnected with the MongoDB: {self.database} successfully")

    def find_one(self, condition: dict, project_vals: dict, collection: str = "admins") -> dict:
        return self.database[collection].find_one(condition, projection=project_vals)

    def find_all(self, condition: dict, project_vals: dict, sort: list = None, collection: str = "admins") -> Any:
        if sort is None:
            sort = [("_id", pymongo.ASCENDING)]
        return (
            self.database[collection]
            .find(condition, projection=project_vals)
            .sort(sort)
        )

    def insert_one(self, model: dict, collection: str = "admins") -> Any:
        return self.database[collection].insert_one(model)

    def update_one(self, condition: dict, new_model: dict, collection: str = "admins") -> dict:
        if model := self.database[collection].find_one_and_update(condition, {"$set": new_model}):
            return self.find_one({"_id": model["_id"]}, {}, collection=collection)

    def delete_one(self, condition: dict, collection: str = "admins") -> Any:
        return self.database[collection].delete_one(condition)
