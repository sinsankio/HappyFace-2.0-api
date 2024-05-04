import copy

from fastapi.encoders import jsonable_encoder
from varname import nameof

from entity.emotion import EmotionExpression
from entity.models import Subject, Message, AuthSubject, SubjectRememberMe
from helper.api.subject_api_helper import SubjectApiHelper
from helper.database.mongodb.db_helper import DbHelper
from helper.datetime.date_time_helper import DateTimeHelper
from helper.hash.hash_helper import HashHelper


class SubjectService:
    @staticmethod
    def authenticate(db_helper: DbHelper, subject: AuthSubject) -> dict | None:
        if auth_organization := db_helper.find_one({"orgKey": subject.org_key}, {}, collection="organizations"):
            subjects = auth_organization["subjects"]

            for sub in subjects:
                if sub["username"] == subject.username and sub["password"] == subject.password:
                    return {"auth_organization": auth_organization, "auth_subject": sub}

    @staticmethod
    def register_all(db_helper: DbHelper, organization_service, organization: dict,
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

    @staticmethod
    def retrieve_all(organization: dict) -> list[dict]:
        return organization["subjects"]

    @staticmethod
    def update(db_helper: DbHelper, organization_service, organization: dict, subject: dict,
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

    @staticmethod
    def delete(db_helper: DbHelper, organization_service, organization: dict, sub_id: str) \
            -> bool:
        old_organization = copy.copy(organization)
        subjects = organization["subjects"]

        for sub in subjects:
            if sub["_id"] == sub_id:
                subjects.remove(sub)
                break

        if _ := organization_service.update(db_helper, old_organization, organization, hashing=False):
            return True

    @staticmethod
    def retrieve_emotion_engagement(db_helper: DbHelper, org_id: str, id: str, **kwargs) -> dict | float | None:
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
            emotion_engagement = {emotion.value: 0 for emotion in EmotionExpression}

            for subject_work_emotion in subject_work_emotions:
                if subject_work_emotion["_id"] == id:
                    work_emotions = subject_work_emotion["workEmotions"]

                    for work_emotion in work_emotions:
                        recorded_on = DateTimeHelper.str_to_iso_datetime(work_emotion["recordedOn"])

                        if work_emotion["accuracy"] >= 80 and recorded_on >= subtracted_iso_datetime:
                            if emotion and work_emotion["expression"] == emotion:
                                emotion_engagement[emotion] += 1
                            else:
                                emotion_engagement[work_emotion["expression"]] += 1

                    if emotion:
                        emotion_engagement = emotion_engagement[emotion] / len(work_emotions)
                    elif work_emotions:
                        emotion_engagement = {key: value / len(work_emotions) for key, value in
                                              emotion_engagement.items()}
                    return emotion_engagement

    @staticmethod
    def retrieve_consultancy(subject: dict) -> dict | None:
        if consultancies := subject["consultancies"]:
            return max(consultancies, key=lambda c: c["consultedOn"])

    @staticmethod
    def build_user_assistant_conversation(db_helper: DbHelper, organization_service, organization, subject: dict,
                                          message: Message) -> dict | None:
        old_subject = copy.copy(subject)
        bio_data_profile = SubjectService.get_bio_data_profile(subject)
        bio_data_profile_summary = SubjectService.get_profile_summary(bio_data_profile)
        if emotion_engagement_profile := SubjectService.get_emotion_engagement_profile(subject["workEmotions"]):
            emotion_engagement_profile_summary = SubjectService.get_profile_summary(emotion_engagement_profile)
            profile_recommendation = SubjectService.get_profile_recommendation(
                bio_data_profile_summary, emotion_engagement_profile_summary
            )
        else:
            profile_recommendation = SubjectService.get_profile_recommendation(
                bio_data_profile_summary, "No emotion engagement profile available"
            )
        if latest_consultancy := SubjectService.retrieve_consultancy(subject):
            if query_consultancy := SubjectApiHelper.get_query_consultancy(
                    message.body,
                    organization["name"],
                    subject["_id"],
                    profile_recommendation,
                    latest_consultancy["chat"]
            ):
                latest_consultancy["chat"].append(message)
                latest_consultancy["chat"].append(Message(body=query_consultancy["emotionistant"]))

                if _ := SubjectService.update(db_helper, organization_service, organization, old_subject, subject,
                                              hashing=False):
                    return SubjectService.retrieve_consultancy(subject)

    @staticmethod
    def get_profile_summary(profile: dict) -> str | None:
        if profile := SubjectApiHelper.get_profile_summary(profile):
            return profile["profileSummary"]

    @staticmethod
    def get_profile_recommendation(bio_data_profile: str, emotion_engagement_profile: dict) -> str | None:
        if recommendation := SubjectApiHelper.get_profile_recommendation(bio_data_profile, emotion_engagement_profile):
            return recommendation["profileRecommendation"]

    @staticmethod
    def get_bio_data_profile(subject: dict) -> dict:
        return {
            "bioDataProfile": {
                "name": subject["name"],
                "address": subject["address"],
                "dateOfBirth": subject["dob"],
                "gender": subject["gender"],
                "salary (USD)": subject["salary"],
                "hiddenDiseases": subject["hiddenDiseases"],
                "familyDetails": {
                    "numberOfMembersInFamily": subject["family"]["numMembers"],
                    "monthlyCumulativeIncomeForFamily(USD)": subject["family"]["monthlyCummIncome"],
                    "monthlyCumulativeExpensesForFamily(USD)": subject["family"]["monthlyCummExpenses"],
                    "numberOfOccupationsWithinFamily": subject["family"]["numOccupations"],
                    "familyCategory": subject["family"]["category"]
                }
            }
        }

    @staticmethod
    def get_classified_work_emotions(work_emotions: list, before_hours=24 * 7) -> tuple[list, list]:
        subtracted_iso_datetime = DateTimeHelper.subtract_iso_datetime(hours=before_hours)
        subtracted_iso_datetime = DateTimeHelper.str_to_iso_datetime(subtracted_iso_datetime)
        facial_emotions = []
        sentimental_emotions = []
        for we in work_emotions:
            if DateTimeHelper.str_to_iso_datetime(we["recordedOn"]) >= subtracted_iso_datetime:
                if "specialConsiderationMessage" in we:
                    sentimental_emotions.append(we)
                else:
                    facial_emotions.append(we)
        return facial_emotions, sentimental_emotions

    @staticmethod
    def analyze_work_emotions(work_emotions: list) -> tuple:
        emotion_engagement = {emotion.value: {"tally": 0, "avg_aro": 0, "avg_val": 0} for emotion in EmotionExpression}
        for emotion in work_emotions:
            emotion_engagement[emotion["expression"]]["tally"] += 1
            emotion_engagement[emotion["expression"]]["avg_aro"] += emotion["arousal"]
            emotion_engagement[emotion["expression"]]["avg_val"] += emotion["valence"]
        for k, v in emotion_engagement.items():
            if emotion_engagement[k]["avg_aro"]:
                emotion_engagement[k]["avg_aro"] /= emotion_engagement[k]["tally"]
            if emotion_engagement[k]["avg_val"]:
                emotion_engagement[k]["avg_val"] /= emotion_engagement[k]["tally"]
        mostly_engaging_emotion = max(emotion_engagement, key=lambda x: emotion_engagement[x]["tally"])
        return emotion_engagement, mostly_engaging_emotion

    @staticmethod
    def get_emotion_engagement_profile(work_emotions: list) -> dict:
        classified_facial_work_emotions, classified_sentimental_work_emotions = (
            SubjectService.get_classified_work_emotions(work_emotions)
        )
        emotion_engagement_profile = {
            "emotionEngagementProfile": {}
        }
        if classified_facial_work_emotions:
            analyzed_facial_emotion_engagement, analyzed_mostly_engaging_facial_emotion = (
                SubjectService.analyze_work_emotions(classified_facial_work_emotions)
            )
            mostly_engaging_facial_emotion_record = {
                "emotion": analyzed_mostly_engaging_facial_emotion,
                "avgArousal(percentage)": analyzed_facial_emotion_engagement[
                    analyzed_mostly_engaging_facial_emotion
                ]["avg_aro"],
                "avgValence(percentage)": analyzed_facial_emotion_engagement[
                    analyzed_mostly_engaging_facial_emotion
                ]["avg_val"]
            }
            emotion_engagement_profile["emotionEngagementProfile"]["mostlyEngagingFacialEmotion"] = (
                mostly_engaging_facial_emotion_record
            )

        if classified_sentimental_work_emotions:
            analyzed_sent_emotion_engagement, analyzed_mostly_engaging_sent_emotion = (
                SubjectService.analyze_work_emotions(classified_sentimental_work_emotions)
            )
            mostly_engaging_sent_emotion_record = {
                "emotion": analyzed_mostly_engaging_sent_emotion,
                "avgArousal(percentage)": analyzed_sent_emotion_engagement[
                    analyzed_mostly_engaging_sent_emotion
                ]["avg_aro"],
                "avgValence(percentage)": analyzed_sent_emotion_engagement[
                    analyzed_mostly_engaging_sent_emotion
                ]["avg_val"]
            }
            emotion_engagement_profile["emotionEngagementProfile"]["mostlyEngagingSentimentalEmotion"] = (
                mostly_engaging_sent_emotion_record
            )
        return emotion_engagement_profile if emotion_engagement_profile[
            "emotionEngagementProfile"] else None

    @staticmethod
    def create_special_consideration_request(request_message: str, org_key: str, subject_id: str) -> dict | None:
        return SubjectApiHelper.request_for_special_consideration_inquiry(request_message, org_key, subject_id)

    @staticmethod
    def remember_me(db_helper: DbHelper, subject_remember_me: SubjectRememberMe) -> dict | None:
        if organization := db_helper.find_one(
                {"orgKey": subject_remember_me.basic_remember_me.auth_key},
                {"_id": False, "subjects": True},
                collection="organizations"
        ):
            subjects = organization["subjects"]

            for subject in subjects:
                if subject["authKey"] == subject_remember_me.sub_auth_key:
                    return subject
