import copy
import uuid

from fastapi.encoders import jsonable_encoder
from varname import nameof

from entity.emotion import Emotion
from entity.models import Message, Consultancy
from entity.models import Organization, WorkEmotionEntry, AuthOrganization, BasicRememberMe
from helper.chat.custom_assistant_response import CustomAssistantResponse
from helper.chat.openai.openai_chat_helper import OpenAiChatHelper
from helper.database.mongodb.db_helper import DbHelper
from helper.datetime.date_time_helper import DateTimeHelper
from helper.hash.hash_helper import HashHelper


class OrganizationService:
    def authenticate(self, db_helper: DbHelper, organization: AuthOrganization) -> dict | None:
        if auth_organization := db_helper.find_one(
                {"orgKey": organization.org_key, "password": organization.password}, {}, collection="organizations"
        ):
            return auth_organization

    def register(self, db_helper: DbHelper, organization: Organization) -> dict:
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

    def retrieve_all(self, db_helper: DbHelper) -> list[dict]:
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
                    work_emotion["emotion"] == Emotion.HAPPY.value
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

    def update(self, db_helper: DbHelper, organization: dict, new_organization: Organization | dict,
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

    def delete(self, db_helper: DbHelper, organization: dict) -> bool:
        if deletion := db_helper.delete_one({"_id": organization["_id"]}, collection="organizations"):
            return deletion.deleted_count >= 1

    def retrieve_emotion_engagement(self, db_helper: DbHelper, org_id: str, **kwargs) -> dict | None:
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
            emotion_engagement = {emotion.value: 0 for emotion in Emotion}
            tot_work_emotions = 0

            for subject_work_emotion in subject_work_emotions:
                work_emotions = subject_work_emotion["workEmotions"]

                for work_emotion in work_emotions:
                    recorded_on = DateTimeHelper.str_to_iso_datetime(work_emotion["recordedOn"])

                    if work_emotion["probability"] >= 80 and recorded_on >= subtracted_iso_datetime:
                        emotion_engagement[work_emotion["emotion"]] += 1
                tot_work_emotions += len(work_emotions)

            if tot_work_emotions > 0:
                return {
                    key: value / tot_work_emotions
                    for key, value in emotion_engagement.items()
                }

    def insert_work_emotion_entries(self, db_helper: DbHelper, org_key: str,
                                    work_emotion_entries: list[WorkEmotionEntry]) -> dict | None:
        if organization := db_helper.find_one({"orgKey": org_key}, {}, collection="organizations"):
            old_organization = copy.copy(organization)
            subjects = organization["subjects"]

            for work_emotion_entry in work_emotion_entries:
                face_snap_dir_uri = work_emotion_entry.face_snap_dir_uri

                for subject in subjects:
                    if subject["faceSnapDirURI"] == face_snap_dir_uri:
                        subject["workEmotions"].extend(jsonable_encoder(work_emotion_entry.work_emotions))
                        break

            if organization := self.update(db_helper, old_organization, organization, hashing=False):
                return organization

    def init_consultancy_services_on_work_emotion_entry_submission(self, db_helper: DbHelper, org_key: str,
                                                                   work_emotion_entries: list[WorkEmotionEntry]) -> bool | None:
        if organization := db_helper.find_one({"orgKey": org_key}, {}, collection="organizations"):
            old_organization = copy.copy(organization)
            subjects = organization["subjects"]

            for work_emotion_entry in work_emotion_entries:
                face_snap_dir_uri = work_emotion_entry.face_snap_dir_uri

                for subject in subjects:
                    if subject["faceSnapDirURI"] == face_snap_dir_uri:
                        subject_id = subject["_id"]
                        subject_work_emotion_entry_tally_count = {subject_id: {}}

                        for work_emotion in work_emotion_entry.work_emotions:
                            if work_emotion.probability >= 80:
                                emotion = work_emotion.emotion.value

                                if emotion in subject_work_emotion_entry_tally_count[subject_id]:
                                    subject_work_emotion_entry_tally_count[subject_id][emotion] += 1
                                else:
                                    subject_work_emotion_entry_tally_count[subject_id][emotion] = 0

                        if work_emotion_tally_count := subject_work_emotion_entry_tally_count[subject_id]:
                            most_engaging_emotion = max(work_emotion_tally_count,
                                                        key=lambda e: work_emotion_tally_count[e]).upper()
                            init_message_content_to_assistant = OpenAiChatHelper.INIT_PROMPT.format(
                                subject["name"], subject["address"], subject["gender"], str(subject["hiddenDiseases"]),
                                subject["salary"], subject["family"]["numMembers"],
                                subject["family"]["monthlyCummIncome"],
                                subject["family"]["monthlyCummExpenses"], subject["family"]["numOccupations"],
                                subject["family"]["category"], most_engaging_emotion
                            )
                            consultancy_id = str(uuid.uuid4())
                            init_message_to_assistant = [
                                {
                                    "role": "user",
                                    "content": init_message_content_to_assistant
                                }
                            ]
                            assistant_response = (OpenAiChatHelper.get_assistant_response(
                                conversation=init_message_to_assistant) or
                                CustomAssistantResponse.RESPONSE_ON_COMPLETION_FAILURE.value)
                            message = Message(
                                body=assistant_response
                            )
                            consultancy = Consultancy(_id=consultancy_id,
                                                      expressionCaused=Emotion[most_engaging_emotion],
                                                      chat=[message])
                            consultancy = jsonable_encoder(consultancy)
                            subject["consultancies"].append(consultancy)
                            break

            if _ := self.update(db_helper, old_organization, organization, hashing=False):
                return True

    def remember_me(self, db_helper: DbHelper, remember_me: BasicRememberMe) -> dict | None:
        if organization := db_helper.find_one({"authKey": remember_me.auth_key}, {}, 
                                              collection="organizations"):
            return organization
