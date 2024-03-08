import copy

from fastapi.encoders import jsonable_encoder
from varname import nameof

from entity.emotion import Emotion
from entity.models import Subject, Message, AuthSubject, SubjectRememberMe
from helper.chat.custom_assistant_response import CustomAssistantResponse
from helper.chat.openai.openai_chat_helper import OpenAiChatHelper
from helper.database.mongodb.db_helper import DbHelper
from helper.datetime.date_time_helper import DateTimeHelper
from helper.hash.hash_helper import HashHelper
from service.organization_service import OrganizationService


class SubjectService:
    def authenticate(self, db_helper: DbHelper, subject: AuthSubject) -> dict | None:
        if auth_organization := db_helper.find_one({"orgKey": subject.org_key}, {}, collection="organizations"):
            subjects = auth_organization["subjects"]

            for sub in subjects:
                if sub["username"] == subject.username and sub["password"] == subject.password:
                    return {"auth_organization": auth_organization, "auth_subject": sub}

    def register_all(self, db_helper: DbHelper, organization_service: OrganizationService, organization: dict,
                     subjects: list[Subject]) -> list[dict]:
        old_organization = copy.copy(organization)

        for subject in subjects:
            subject.username = HashHelper.hash(subject.username)
            subject.password = HashHelper.hash(subject.password)
            subject.auth_key = HashHelper.hash(subject.auth_key)

        subjects = jsonable_encoder(subjects)
        organization["subjects"].extend(subjects)

        if _ := organization_service.update(db_helper, old_organization, organization, hashing=False):
            return subjects

    def retrieve_all(self, organization: dict) -> list[dict]:
        return organization["subjects"]

    def update(self, db_helper: DbHelper, organization_service: OrganizationService, organization: dict, subject: dict,
               new_subject: dict, hashing=True) -> dict:
        old_organization = copy.copy(organization)
        subjects = organization["subjects"]
        new_jsonable_subject = jsonable_encoder(new_subject)
        new_jsonable_subject["_id"] = subject["_id"]

        if hashing:
            new_jsonable_subject["username"] = HashHelper.hash(new_jsonable_subject["username"])
            new_jsonable_subject["password"] = HashHelper.hash(new_jsonable_subject["password"])
            new_jsonable_subject["authKey"] = HashHelper.hash(new_jsonable_subject["authKey"])
        else:
            new_jsonable_subject["username"] = subject["username"]
            new_jsonable_subject["password"] = subject["password"]

        for i in range(len(subjects)):
            if subjects[i]["_id"] == subject["_id"]:
                subjects[i] = new_jsonable_subject
                break

        if _ := organization_service.update(db_helper, old_organization, organization, hashing=False):
            return new_jsonable_subject

    def delete(self, db_helper: DbHelper, organization_service: OrganizationService, organization: dict, sub_id: str) \
            -> bool:
        old_organization = copy.copy(organization)
        subjects = organization["subjects"]

        for sub in subjects:
            if sub["_id"] == sub_id:
                subjects.remove(sub)
                break

        if _ := organization_service.update(db_helper, old_organization, organization, hashing=False):
            return True

    def retrieve_emotion_engagement(self, db_helper: DbHelper, org_id: str, id: str, **kwargs) -> dict | float | None:
        hours = weeks = months = years = 0
        emotion = None

        if kwargs[nameof(hours)]:
            hours = abs(int(kwargs[nameof(hours)]))
        if kwargs[nameof(weeks)]:
            weeks = abs(int(kwargs[nameof(weeks)]))
        if kwargs[nameof(months)]:
            months = abs(int(kwargs[nameof(months)]))
        if kwargs[nameof(years)]:
            years = abs(int(kwargs[nameof(years)]))
        if nameof(emotion) in kwargs:
            emotion = kwargs[nameof(emotion)]

        if subjects := db_helper.find_one(
            {"_id": org_id},
            {"_id": False, "subjects": {"_id": True, "workEmotions": True}},
            collection="organizations",
        ):
            subject_work_emotions = subjects["subjects"]
            subtracted_iso_datetime = DateTimeHelper.subtract_iso_datetime(hours, weeks, months, years)
            subtracted_iso_datetime = DateTimeHelper.str_to_iso_datetime(subtracted_iso_datetime)
            emotion_engagement = {emotion.value: 0 for emotion in Emotion}

            for subject_work_emotion in subject_work_emotions:
                if subject_work_emotion["_id"] == id:
                    work_emotions = subject_work_emotion["workEmotions"]

                    for work_emotion in work_emotions:
                        recorded_on = DateTimeHelper.str_to_iso_datetime(work_emotion["recordedOn"])

                        if work_emotion["probability"] >= 80 and recorded_on >= subtracted_iso_datetime:
                            if emotion and work_emotion["emotion"] == emotion:
                                emotion_engagement[emotion] += 1
                            else:
                                emotion_engagement[work_emotion["emotion"]] += 1

                    if emotion:
                        emotion_engagement = emotion_engagement[emotion] / len(work_emotions)
                    elif work_emotions:
                        emotion_engagement = {key: value / len(work_emotions) for key, value in emotion_engagement.items()}
                    return emotion_engagement

    def retrieve_consultancy(self, subject: dict) -> dict | None:
        if consultancies := subject["consultancies"]:
            return max(consultancies, key=lambda c: c["consultedOn"])

    def build_user_assistant_conversation(self, db_helper: DbHelper, organization_service: OrganizationService,
                                          organization, subject: dict, message: Message) -> dict | None:
        old_subject = copy.copy(subject)

        if consultancies := subject["consultancies"]:
            latest_consultancy = max(consultancies, key=lambda c: c["consultedOn"])
            latest_consultancy_chat = latest_consultancy["chat"]
            latest_consultancy_conversation = []

            for chat in latest_consultancy_chat:
                record = {
                    "role": chat["sender"],
                    "content": chat["body"]
                }
                latest_consultancy_conversation.append(record)

            validity = OpenAiChatHelper.validate_user_message(message=message.body)
            if type(validity) is bool:
                if validity:
                    message_dict = {
                        "role": "user",
                        "content": message.body
                    }
                    latest_consultancy_conversation.append(message_dict)

                    assistant_reply_message_content = OpenAiChatHelper.get_assistant_response(
                                    conversation=latest_consultancy_conversation
                                ) or CustomAssistantResponse.RESPONSE_ON_COMPLETION_FAILURE.value
                else:
                    assistant_reply_message_content = CustomAssistantResponse.RESPONSE_ON_DOMAIN_MISMATCH.value
            else:
                assistant_reply_message_content = CustomAssistantResponse.RESPONSE_ON_COMPLETION_FAILURE.value

            assistant_reply_message = Message(body=assistant_reply_message_content)
            message.sender = "user"
            message.receiver = "assistant"
            latest_consultancy_chat.append(jsonable_encoder(message))
            latest_consultancy_chat.append(jsonable_encoder(assistant_reply_message))

            if _ := self.update(db_helper, organization_service, organization, old_subject, subject, hashing=False):
                return self.retrieve_consultancy(subject)

    def remember_me(self, db_helper: DbHelper, subject_remember_me: SubjectRememberMe) -> dict | None:
        if organization := db_helper.find_one(
            {"orgKey": subject_remember_me.basic_remember_me.auth_key}, {"_id": False, "subjects": True},
            collection="organizations"
        ):
            subjects = organization["subjects"]

            for subject in subjects:
                if subject["authKey"] == subject_remember_me.sub_auth_key:
                    return subject
