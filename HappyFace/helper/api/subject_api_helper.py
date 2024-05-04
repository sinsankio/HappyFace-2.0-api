from helper.api.config_helper import ConfigHelper
from helper.api.request_helper import RequestHelper, HttpRequest


class SubjectApiHelper:
    @staticmethod
    def get_profile_summary(profile: dict) -> dict | None:
        url = ConfigHelper.SUBJECT_PROFILE_SUMMARIZE_ENDPOINT
        data = {
            "profile": profile
        }

        if summarization := RequestHelper.perform_request(HttpRequest.POST, url, data):
            return summarization

    @staticmethod
    def get_profile_recommendation(bio_data_profile: str, emotion_engagement_profile: str) -> dict | None:
        url = ConfigHelper.SUBJECT_PROFILES_TO_RECOMMENDATION
        data = {
            "bioDataProfile": bio_data_profile,
            "emotionEngagementProfile": emotion_engagement_profile
        }

        if recommendation := RequestHelper.perform_request(HttpRequest.POST, url, data):
            return recommendation

    @staticmethod
    def get_init_consultancy(bio_data_profile: str, emotion_engagement_profile: str) -> dict | None:
        url = ConfigHelper.SUBJECT_INIT_CONSULTANCY
        data = {
            "bioDataProfile": bio_data_profile,
            "emotionEngagementProfile": emotion_engagement_profile
        }

        if consultation := RequestHelper.perform_request(HttpRequest.POST, url, data):
            return consultation["emotionistant"]

    @staticmethod
    def get_query_consultancy(query: str, organization_name: str, employee_id: str, profile_recommendation: str,
                              chat_history: list) -> dict | None:
        url = ConfigHelper.SUBJECT_QUERY_CONSULTANCY
        data = {
            "query": query,
            "organizationName": organization_name,
            "employeeId": employee_id,
            "profileRecommendation": profile_recommendation,
            "chatHistory": chat_history
        }

        if consultation := RequestHelper.perform_request(HttpRequest.POST, url, data):
            return consultation

    @staticmethod
    def request_for_special_consideration_inquiry(request_message: str, org_key: str, subject_id: str) -> dict | None:
        url = ConfigHelper.SUBJECT_SPECIAL_CONSIDERATION_INQUIRY
        data = {
            "orgKey": org_key,
            "subjectId": subject_id,
            "specialConsiderationMessage": request_message
        }

        if analysis := RequestHelper.perform_request(HttpRequest.POST, url, data):
            return analysis
