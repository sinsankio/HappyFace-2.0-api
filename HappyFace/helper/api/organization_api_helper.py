from helper.api.config_helper import ConfigHelper
from helper.api.request_helper import RequestHelper, HttpRequest


class OrganizationApiHelper:
    @staticmethod
    def get_organizational_sentimental_emotions(org_key: str) -> dict | None:
        url = ConfigHelper.ORGANIZATION_EMOTION_ENDPOINT
        data = {
            "orgKey": org_key
        }

        if emotions := RequestHelper.perform_request(HttpRequest.POST, url, data):
            return emotions

    @staticmethod
    def delete_organizational_sentimental_emotions(org_key: str) -> int:
        url = ConfigHelper.ORGANIZATION_EMOTION_ENDPOINT
        data = {
            "orgKey": org_key
        }

        if deletion := RequestHelper.perform_request(HttpRequest.DELETE, url, data):
            return deletion
