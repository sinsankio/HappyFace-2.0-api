import uuid
from typing import Union

from pydantic import Field, BaseModel

from entity.emotion import EmotionExpression
from entity.gender import Gender
from helper.datetime.date_time_helper import DateTimeHelper
from helper.key.random_key_helper import RandomKeyHelper
from helper.media.image.image_helper import ImageHelper


class Admin(BaseModel):
    id: str = Field(default="bb4be6e1-33f3-4a7c-8d19-438fcfe947c4", alias="_id")
    username: str
    password: str
    created_on: str = Field(default_factory=DateTimeHelper.get_current_iso_datetime, alias="createdOn")
    auth_key: str | None = Field(default=None, alias="authKey")


class AuthAdmin(BaseModel):
    username: str
    password: str


class Emotionistant(BaseModel):
    id: str = Field(default="015b8e2b-b470-44ac-8201-cf4fd12e12d3", alias="_id")
    publisher: str = Field(default="HappyFace")
    name: str = Field(default="HappyFace-Emotionistant")
    version: str = Field(default="1.0")
    features: list[str] = Field(default=list())
    limitations: list[str] = Field(default=list())
    tech_specs: list[str] = Field(default=list(), alias="techSpecs")


class EmotionRecognizer(BaseModel):
    id: str = Field(default="b625225a-b107-4e1d-870d-02f49be01ac3", alias="_id")
    publisher: str = Field(default="HappyFace")
    name: str = Field(default="FER")
    version: str = Field(default="1.0")
    features: list[str] = Field(default=list())
    limitations: list[str] = Field(default=list())
    tech_specs: list[str] = Field(default=list(), alias="techSpecs")


class FaceDetector(BaseModel):
    id: str = Field(default="5cbab45e-5b74-4607-92ac-8c93101f5913", alias="_id")
    publisher: str = Field(default="Google")
    name: str = Field(default="MediaPipe")
    version: str = Field(default="latest")
    features: list[str] = Field(default=list())
    limitations: list[str] = Field(default=list())
    tech_specs: list[str] = Field(default=list(), alias="techSpecs")


class FaceMatcher(BaseModel):
    id: str = Field(default="881a28ee-a034-4c94-b9f6-8e4825085b94", alias="_id")
    publisher: str = Field(default="Adam Geitgey")
    name: str = Field(default="Face-Recognition")
    version: str = Field(default="latest")
    features: list[str] = Field(default=list())
    limitations: list[str] = Field(default=list())
    tech_specs: list[str] = Field(default=list(), alias="techSpecs")


class Family(BaseModel):
    num_members: int = Field(default=1, ge=1, alias="numMembers")
    monthly_cumm_income: int = Field(default=10, ge=1, alias="monthlyCummIncome")
    monthly_cumm_expenses: int = Field(default=5, ge=1, alias="monthlyCummExpenses")
    num_occupations: int = Field(default=1, ge=1, alias="numOccupations")
    category: str = Field(default="nuclear")


class SpecialConsiderationRequest(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    message: str = Field()
    response: str | None = Field(default=None)
    requested_on: str = Field(default_factory=DateTimeHelper.get_current_iso_datetime, alias="requestedOn")
    responded_on: str | None = Field(default=None, alias="respondedOn")


class SpecialConsiderationRequestEntry(BaseModel):
    subject_id: str = Field(alias="subjectId")
    request_id: str = Field(alias="requestId")
    subject_name: str = Field(alias="subjectName")
    message: str = Field()
    requested_on: str = Field(alias="requestedOn")


class SpecialConsiderationResponseEntry(BaseModel):
    request_id: str = Field(alias="requestId")
    subject_id: str = Field(alias="subjectId")
    message: str = Field()
    responded_on: str = Field(default_factory=DateTimeHelper.get_current_iso_datetime, alias="respondedOn")


class HumanFacialEmotion(BaseModel):
    expression: EmotionExpression = Field(default=EmotionExpression.HAPPY.value)
    accuracy: float = Field(default=100)
    arousal: float = Field(le=100, ge=-100)
    valence: float = Field(le=100, ge=-100)
    recorded_on: str = Field(default_factory=DateTimeHelper.get_current_iso_datetime, alias="recordedOn")


class HumanSentimentalEmotion(BaseModel):
    expression: EmotionExpression = Field(default=EmotionExpression.HAPPY.value)
    accuracy: float = Field(default=100)
    arousal: float = Field(le=100, ge=-100)
    valence: float = Field(le=100, ge=-100)
    special_consideration_msg: str = Field(alias="specialConsiderationMessage")
    recorded_on: str = Field(default_factory=DateTimeHelper.get_current_iso_datetime, alias="recordedOn")


class FacialWorkEmotionEntry(BaseModel):
    face_snap_dir_uri: str = Field(alias="faceSnapDirURI")
    created_on: str = Field(default_factory=DateTimeHelper.get_current_iso_datetime, alias="createdOn")
    work_emotions: list[HumanFacialEmotion] = Field(default=[], alias="workEmotions")


class SentimentalEmotionEntry(BaseModel):
    id: str = Field(alias="_id")
    org_key: str = Field(alias="orgKey")
    subject_id: str = Field(alias="subjectId")
    last_update_on: str = Field(default_factory=DateTimeHelper.get_current_iso_datetime, alias="lastUpdateOn")
    work_emotions: list[HumanSentimentalEmotion] = Field(default=[], alias="workEmotions")


class Message(BaseModel):
    sender: str = Field(default="emotionistant")
    receiver: str = Field(default="friend")
    body: str
    sent_on: str = Field(default_factory=DateTimeHelper.get_current_iso_datetime, alias="sentOn")


class EmotionistantConsultancy(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    chat: list[Message] = Field(default=list())
    consulted_on: str = Field(default_factory=DateTimeHelper.get_current_iso_datetime, alias="consultedOn")


class Subject(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    username: str = Field(min_length=10)
    password: str = Field(min_length=10)
    name: str = Field(max_length=20)
    address: str = Field(default="Sri Lanka")
    dob: str = Field()
    gender: Gender = Field(default=Gender.MALE)
    email: str = Field()
    registered_on: str = Field(default_factory=DateTimeHelper.get_current_iso_datetime, alias="registeredOn")
    display_photo: str = Field(default=ImageHelper.get_default_org_logo(), alias="displayPhoto")
    salary: int = Field()
    hidden_diseases: list[str] = Field(default=list(), alias="hiddenDiseases")
    family: Family | dict = Field(default=Family().model_dump())
    face_snap_dir_uri: str = Field(alias="faceSnapDirURI")
    work_emotions: list[Union[HumanSentimentalEmotion, HumanFacialEmotion]] = Field(default=list(),
                                                                                    alias="workEmotions")
    consultancies: list[EmotionistantConsultancy] = Field(default=list())
    special_consideration_requests: list[SpecialConsiderationRequest] = Field(default=list(),
                                                                              alias="specialConsiderationRequests")
    auth_key: str | None = Field(default=None, alias="authKey")


class AuthSubject(BaseModel):
    username: str
    password: str
    org_key: str = Field(alias="orgKey")


class AdministrativeSubject(BaseModel):
    id: str = Field(default=str(uuid.uuid4()), alias="_id")


class Thread(BaseModel):
    message: str | None = Field(default=None)
    published_on: str = Field(default_factory=DateTimeHelper.get_current_iso_datetime, alias="publishedOn")


class Subscription(BaseModel):
    id: str = Field(default="3aefea00-6bae-4498-a0c2-17fc0f87a1ea", alias="_id")
    name: str = Field(default="essential", max_length=10)
    price: float = Field(default=100, ge=100)
    introduced_on: str = Field(default="2023-04-01T00:00:00.000001", alias="introducedOn")
    face_detector: FaceDetector | dict = Field(default=FaceDetector().model_dump(), alias="faceDetector")
    face_matcher: FaceMatcher | dict = Field(default=FaceMatcher().model_dump(), alias="faceMatcher")
    emotion_recognizer: EmotionRecognizer | dict = Field(default=EmotionRecognizer().model_dump(),
                                                         alias="emotionRecognizer")
    assistant: Emotionistant | dict = Field(default=Emotionistant().model_dump())
    additional_features: list[str] = Field(default=list(), alias="additionalFeatures")


class Organization(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    name: str = Field(max_length=50)
    address: str = Field(max_length=100)
    business_registration: str | None = Field(default=None, max_length=50, alias="businessReg")
    owner: str | None = Field(default=None, max_length=50)
    registered_on: str = Field(default_factory=DateTimeHelper.get_current_iso_datetime, alias="registeredOn")
    display_logo: str = Field(default=ImageHelper.get_default_org_logo(), alias="displayLogo")
    email: str = Field()
    subjects: list[Subject] = Field(default=list())
    threads: list[Thread] = Field(default=list())
    org_key: str = Field(default_factory=RandomKeyHelper.generate_random_key, min_length=10, alias="orgKey")
    password: str = Field(min_length=10)
    subscription: Subscription | dict = Field(default=Subscription().model_dump())
    auth_key: str | None = Field(default=None, alias="authKey")


class AuthOrganization(BaseModel):
    org_key: str = Field(default="", alias="orgKey")
    password: str = Field(default="")


class AdministrativeOrganization(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    name: str = Field(max_length=50)
    address: str = Field(max_length=100)
    business_registration: str | None = Field(default=None, max_length=50, alias="businessReg")
    owner: str | None = Field(default=None, max_length=50)
    registered_on: str = Field(default_factory=DateTimeHelper.get_current_iso_datetime, alias="registeredOn")
    display_logo: str = Field(default_factory=ImageHelper.get_default_org_logo, alias="displayLogo")
    email: str = Field()
    subjects: list[AdministrativeSubject] = Field(default=list())
    happy_engagement: float = Field(default=0, alias="happyEngagement")
    subscription: Subscription | dict = Field(default=Subscription().model_dump())


class BasicRememberMe(BaseModel):
    auth_key: str = Field(alias="authKey")


class SubjectRememberMe(BaseModel):
    basic_remember_me: BasicRememberMe = Field(alias="basicRememberMe")
    sub_auth_key: str = Field(alias="subAuthKey")
