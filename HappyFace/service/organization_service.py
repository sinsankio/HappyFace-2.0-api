import copy
import uuid

from fastapi.encoders import jsonable_encoder
from varname import nameof

from entity.emotion import EmotionExpression
from entity.models import EmotionistantConsultancy
from entity.models import Message
from entity.models import (
    Organization, FacialWorkEmotionEntry, AuthOrganization, BasicRememberMe, SpecialConsiderationRequestEntry,
    SpecialConsiderationRequest
)
from helper.api.subject_api_helper import SubjectApiHelper
from helper.database.mongodb.db_helper import DbHelper
from helper.datetime.date_time_helper import DateTimeHelper
from helper.hash.hash_helper import HashHelper
from service.subject_service import SubjectService


class OrganizationService:
    @staticmethod
    def authenticate(db_helper: DbHelper, organization: AuthOrganization) -> dict | None:
        if auth_organization := db_helper.find_one(
                {"orgKey": organization.org_key, "password": organization.password}, {}, collection="organizations"
        ):
            return auth_organization

    @staticmethod
    def register(db_helper: DbHelper, organization: Organization) -> dict:
        organization_key = organization.org_key
        organization.org_key = HashHelper.hash(organization.org_key)
        organization.password = HashHelper.hash(organization.password)
        organization.auth_key = HashHelper.hash(organization.auth_key)
        jsonable_organization = jsonable_encoder(organization)
        organization_insertion = db_helper.insert_one(jsonable_organization, collection="organizations")
        registered_organization = db_helper.find_one(
            {"_id": organization_insertion.inserted_id},
            {},
            collection="organizations"
        )
        registered_organization["orgKey"] = organization_key
        return registered_organization

    @staticmethod
    def retrieve_all(db_helper: DbHelper) -> list[dict]:
        projection = {
            "name": True,
            "address": True,
            "businessReg": True,
            "owner": True,
            "registeredOn": True,
            "displayLogo": True,
            "email": True,
            "subjects": {
                "_id": True,
                "workEmotions": True
            },
            "subscription": True
        }
        organization_result = db_helper.find_all({}, projection, collection="organizations")
        organizations = list(organization_result)

        for organization in organizations:
            subjects = organization["subjects"]
            happy_engagement = 0

            for subject in subjects:
                work_emotions = subject["workEmotions"]
                subject_happy_engagement = sum(
                    work_emotion["expression"] == EmotionExpression.HAPPY.value
                    for work_emotion in work_emotions
                )
                if work_emotions:
                    subject_happy_engagement /= len(work_emotions)
                happy_engagement += subject_happy_engagement
                del subject["workEmotions"]

            if subjects:
                happy_engagement /= len(subjects)
            organization["happyEngagement"] = happy_engagement

        if organizations:
            organizations = sorted(organizations, key=lambda org: org["happyEngagement"], reverse=True)
        return organizations

    @staticmethod
    def update(db_helper: DbHelper, organization: dict, new_organization: Organization | dict,
               hashing=True) -> dict:
        new_jsonable_organization = jsonable_encoder(new_organization)
        new_jsonable_organization["_id"] = organization["_id"]

        if hashing:
            new_jsonable_organization["orgKey"] = HashHelper.hash(new_jsonable_organization["orgKey"])
            new_jsonable_organization["password"] = HashHelper.hash(new_jsonable_organization["password"])
            new_jsonable_organization["authKey"] = HashHelper.hash(new_jsonable_organization["authKey"])
        else:
            new_jsonable_organization["orgKey"] = organization["orgKey"]
            new_jsonable_organization["password"] = organization["password"]

        if organization := db_helper.update_one({"_id": organization["_id"]}, new_jsonable_organization,
                                                collection="organizations"):
            return organization

    @staticmethod
    def delete(db_helper: DbHelper, organization: dict) -> bool:
        if deletion := db_helper.delete_one({"_id": organization["_id"]}, collection="organizations"):
            return deletion.deleted_count >= 1

    def insert_facial_work_emotion_entries(self, db_helper: DbHelper, org_key: str,
                                           facial_work_emotion_entries: list[FacialWorkEmotionEntry]) -> dict | None:
        if organization := db_helper.find_one({"orgKey": org_key}, {}, collection="organizations"):
            old_organization = copy.copy(organization)
            subjects = organization["subjects"]
            face_snap_dir_subjects = {}

            for subject in subjects:
                face_snap_dir_subjects[subject["faceSnapDirURI"]] = subject

            for entry in facial_work_emotion_entries:
                if subject := face_snap_dir_subjects[entry.face_snap_dir_uri]:
                    subject["workEmotions"].extend(jsonable_encoder(entry.work_emotions))

            if organization := self.update(db_helper, old_organization, organization, hashing=False):
                return organization

    def insert_sentimental_work_emotion_entries(self, db_helper: DbHelper, org_key: str,
                                                sentimental_work_emotion_entries: list[dict]) \
            -> dict | None:
        if organization := db_helper.find_one({"orgKey": org_key}, {}, collection="organizations"):
            old_organization = copy.copy(organization)
            subjects = organization["subjects"]
            id_subjects = {}

            for subject in subjects:
                id_subjects[subject["_id"]] = subject

            for entry in sentimental_work_emotion_entries:
                if subject := id_subjects[entry["subjectId"]]:
                    new_work_emotions = jsonable_encoder(entry["workEmotions"])
                    subject["workEmotions"].extend(new_work_emotions)
                    for we in new_work_emotions:
                        if "specialConsiderationMessage" in we:
                            subject["specialConsiderationRequests"].append(
                                jsonable_encoder(
                                    SpecialConsiderationRequest(
                                        message=we["specialConsiderationMessage"],
                                        requestedOn=we["recordedOn"]
                                    )
                                )
                            )

            if organization := self.update(db_helper, old_organization, organization, hashing=False):
                return organization

    @staticmethod
    def init_consultancy_services_on_latest_work_emotion_entries(db_helper: DbHelper, org_key: str) -> bool | None:
        if organization := db_helper.find_one({"orgKey": org_key}, {}, collection="organizations"):
            old_organization = copy.copy(organization)
            subjects = organization["subjects"]
            for subject in subjects:
                bio_data_profile = SubjectService.get_bio_data_profile(subject)
                bio_data_profile_summary = SubjectService.get_profile_summary(bio_data_profile)
                if emotion_engagement_profile := SubjectService.get_emotion_engagement_profile(
                        subject["workEmotions"]):
                    emotion_engagement_profile_summary = SubjectService.get_profile_summary(
                        emotion_engagement_profile)
                else:
                    emotion_engagement_profile_summary = "No emotion engagement profile available"
                if consultation := SubjectApiHelper.get_init_consultancy(
                        bio_data_profile_summary,
                        emotion_engagement_profile_summary
                ):
                    message = Message(body=consultation)
                    consultancy = EmotionistantConsultancy(_id=str(uuid.uuid4()), chat=[message])
                    consultancy = jsonable_encoder(consultancy)
                    subject["consultancies"].append(consultancy)
            if organization := OrganizationService.update(db_helper, old_organization, organization, hashing=False):
                return organization

    @staticmethod
    def remember_me(db_helper: DbHelper, remember_me: BasicRememberMe) -> dict | None:
        if organization := db_helper.find_one({"authKey": remember_me.auth_key}, {},
                                              collection="organizations"):
            return organization

    @staticmethod
    def retrieve_emotion_engagement(db_helper: DbHelper, org_id: str, **kwargs) -> dict | None:
        hours = weeks = months = years = 0

        if kwargs[nameof(hours)]:
            hours = abs(int(kwargs[nameof(hours)]))
        if kwargs[nameof(weeks)]:
            weeks = abs(int(kwargs[nameof(weeks)]))
        if kwargs[nameof(months)]:
            months = abs(int(kwargs[nameof(months)]))
        if kwargs[nameof(years)]:
            years = abs(int(kwargs[nameof(years)]))

        if subjects := db_helper.find_one({"_id": org_id},
                                          {"_id": False, "subjects": {"workEmotions": True}},
                                          collection="organizations"):
            subject_work_emotions = subjects["subjects"]
            subtracted_iso_datetime = DateTimeHelper.subtract_iso_datetime(hours, weeks, months, years)
            subtracted_iso_datetime = DateTimeHelper.str_to_iso_datetime(subtracted_iso_datetime)
            emotion_engagement = {emotion.value: 0 for emotion in EmotionExpression}
            tot_work_emotions = 0

            for subject_work_emotion in subject_work_emotions:
                work_emotions = subject_work_emotion["workEmotions"]

                for work_emotion in work_emotions:
                    recorded_on = DateTimeHelper.str_to_iso_datetime(work_emotion["recordedOn"])

                    if work_emotion["accuracy"] >= 80 and recorded_on >= subtracted_iso_datetime:
                        emotion_engagement[work_emotion["expression"]] += 1
                tot_work_emotions += len(work_emotions)

            if tot_work_emotions > 0:
                return {
                    key: value / tot_work_emotions
                    for key, value in emotion_engagement.items()
                }

    @staticmethod
    def retrieve_unresponded_special_consideration_requests(organization: dict) -> list:
        unresponded_requests = []
        for subject in organization["subjects"]:
            for request in subject["specialConsiderationRequests"]:
                if not request["response"]:
                    special_consideration_request_entry = SpecialConsiderationRequestEntry(
                        subjectId=subject["_id"],
                        requestId=request["_id"],
                        subjectName=subject["name"],
                        message=request["message"],
                        requestedOn=request["requestedOn"]
                    )
                    unresponded_requests.append(special_consideration_request_entry)
        return unresponded_requests

    @staticmethod
    def write_response_for_special_consideration_requests(db_helper: DbHelper, organization: dict,
                                                          special_consideration_responses: list) -> dict:
        old_organization = copy.copy(organization)
        id_subject_sc_requests = {}
        for subject in organization["subjects"]:
            subject_id = subject["_id"]
            id_subject_sc_requests[subject_id] = {"subject": subject, "sc_requests": []}
            for request in subject["specialConsiderationRequests"]:
                if request["response"] is None:
                    id_subject_sc_requests[subject_id]["sc_requests"].append(request)

        for response in special_consideration_responses:
            response = jsonable_encoder(response)
            response_subject_id = response["subjectId"]
            if response_subject_id in id_subject_sc_requests:
                id_subject_sc_request = id_subject_sc_requests[response_subject_id]
                for request in id_subject_sc_request["sc_requests"]:
                    if request["_id"] == response["requestId"]:
                        request["response"] = response["message"]
                        request["respondedOn"] = response["respondedOn"]

        if organization := OrganizationService.update(db_helper, old_organization, organization, hashing=False):
            return organization
