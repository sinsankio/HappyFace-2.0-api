from fastapi import APIRouter, Request, HTTPException, status, Query, Body

from entity.emotion import EmotionExpression
from entity.models import Subject, EmotionistantConsultancy, Message, AuthSubject, SubjectRememberMe, \
    SpecialConsiderationRequest

router = APIRouter()


@router.post("", response_description="subject retrieval", status_code=status.HTTP_200_OK, response_model=Subject)
async def fetch_subject(request: Request, subject: AuthSubject = Body(...)) -> dict:
    db_helper = request.app.db_helper
    auth_service = request.app.auth_service
    subject_service = request.app.subject_service

    if auth_org_subject := auth_service.auth_subject(db_helper, subject_service, subject):
        return auth_org_subject["auth_subject"]
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized request")


@router.put("", response_description="subject modification", status_code=status.HTTP_200_OK,
            response_model=Subject)
async def update_subject(request: Request, subject: AuthSubject = Body(...),
                         new_subject: Subject = Body(..., alias="newSubject")) -> dict:
    db_helper = request.app.db_helper
    auth_service = request.app.auth_service
    subject_service = request.app.subject_service
    organization_service = request.app.organization_service

    if auth_org_subject := auth_service.auth_subject(db_helper, subject_service, subject):
        auth_organization = auth_org_subject["auth_organization"]
        auth_subject = auth_org_subject["auth_subject"]

        if updated_subject := subject_service.update(db_helper, organization_service, auth_organization, auth_subject,
                                                     new_subject, hashing=False):
            return updated_subject
        raise HTTPException(status_code=status.HTTP_304_NOT_MODIFIED, detail="subject modification failed")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized request")


@router.put("/credentials", response_description="subject credential modification", status_code=status.HTTP_200_OK,
            response_model=Subject)
async def update_subject_with_credentials(request: Request, subject: AuthSubject = Body(...),
                                          new_subject: Subject = Body(..., alias="newSubject")) -> dict:
    db_helper = request.app.db_helper
    auth_service = request.app.auth_service
    subject_service = request.app.subject_service
    organization_service = request.app.organization_service

    if auth_org_subject := auth_service.auth_subject(db_helper, subject_service, subject):
        auth_organization = auth_org_subject["auth_organization"]
        auth_subject = auth_org_subject["auth_subject"]

        if updated_subject := subject_service.update(db_helper, organization_service, auth_organization, auth_subject,
                                                     new_subject):
            return updated_subject
        raise HTTPException(status_code=status.HTTP_304_NOT_MODIFIED, detail="subject modification failed")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized request")


@router.post("/emotions", response_description="emotion engagement retrieval", status_code=status.HTTP_200_OK)
async def fetch_emotion_engagement(request: Request, subject: AuthSubject = Body(...),
                                   hours: int = Query(None, description="hours before"),
                                   weeks: int = Query(None, description="weeks before"),
                                   months: int = Query(None, description="months before"),
                                   years: int = Query(None, description="years before"),
                                   emotion: str = Query(None, description="based emotion")) -> dict | float:
    db_helper = request.app.db_helper
    auth_service = request.app.auth_service
    subject_service = request.app.subject_service

    if auth_org_subject := auth_service.auth_subject(db_helper, subject_service, subject):
        org_id = auth_org_subject["auth_organization"]["_id"]
        sub_id = auth_org_subject["auth_subject"]["_id"]

        if emotion:
            try:
                emotion = emotion.upper()
                emotion = EmotionExpression[emotion].value
                emotional_engagement = subject_service.retrieve_emotion_engagement(db_helper, org_id, sub_id,
                                                                                   hours=hours,
                                                                                   weeks=weeks, months=months,
                                                                                   years=years,
                                                                                   emotion=emotion)
            except KeyError as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="emotion not available",
                ) from e
        else:
            emotional_engagement = subject_service.retrieve_emotion_engagement(db_helper, org_id, sub_id, hours=hours,
                                                                               weeks=weeks, months=months, years=years)
        if emotional_engagement:
            return emotional_engagement
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="emotion engagement not available")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized request")


@router.post("/consultation",
             response_description="assistant consultation retrieval",
             status_code=status.HTTP_200_OK,
             response_model=EmotionistantConsultancy)
async def fetch_consultancy(request: Request, subject: AuthSubject = Body(...)) -> dict:
    db_helper = request.app.db_helper
    auth_service = request.app.auth_service
    subject_service = request.app.subject_service

    if auth_org_subject := auth_service.auth_subject(db_helper, subject_service, subject):
        auth_subject = auth_org_subject["auth_subject"]

        if consultancy := subject_service.retrieve_consultancy(auth_subject):
            return consultancy
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="consultancy not available")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized request")


@router.post("/consultation/chat", response_description="chat with assistant", status_code=status.HTTP_200_OK)
async def chat_with_assistant(request: Request, subject: AuthSubject = Body(...),
                              message: Message = Body(...)) -> dict:
    db_helper = request.app.db_helper
    auth_service = request.app.auth_service
    subject_service = request.app.subject_service
    organization_service = request.app.organization_service

    if auth_org_subject := auth_service.auth_subject(db_helper, subject_service, subject):
        auth_organization = auth_org_subject["auth_organization"]
        auth_subject = auth_org_subject["auth_subject"]

        if conversation := subject_service.build_user_assistant_conversation(db_helper, organization_service,
                                                                             auth_organization, auth_subject, message):
            return conversation
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="chat with assistant failed")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized request")


@router.post("/scr", response_description="request a special consideration", status_code=status.HTTP_200_OK)
async def request_special_consideration(request: Request, subject: AuthSubject = Body(...),
                                        special_consideration_request: SpecialConsiderationRequest =
                                        Body(..., alias="specialConsiderationRequest")) -> dict:
    db_helper = request.app.db_helper
    auth_service = request.app.auth_service
    subject_service = request.app.subject_service

    if auth_org_subject := auth_service.auth_subject(db_helper, subject_service, subject):
        auth_organization = auth_org_subject["auth_organization"]
        auth_subject = auth_org_subject["auth_subject"]

        if analysis := subject_service.create_special_consideration_request(
                special_consideration_request.message,
                auth_organization["orgKey"],
                auth_subject["_id"]
        ):
            return analysis
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="special consideration request failed")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized request")


@router.post(
    "/scr-responses",
    response_description="fetch responded special consideration requests",
    status_code=status.HTTP_200_OK,
    response_model=list[SpecialConsiderationRequest])
async def fetch_responded_special_consideration_requests(request: Request, subject: AuthSubject = Body(...)) -> dict:
    db_helper = request.app.db_helper
    auth_service = request.app.auth_service
    subject_service = request.app.subject_service

    if auth_org_subject := auth_service.auth_subject(db_helper, subject_service, subject):
        auth_subject = auth_org_subject["auth_subject"]
        return subject_service.fetch_responded_special_consideration_requests(auth_subject)
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized request")


@router.post("/remember", response_description="subject remember me", status_code=status.HTTP_200_OK,
             response_model=Subject)
async def remember_me(request: Request, subject_remember_me: SubjectRememberMe = Body(...)) -> list[dict]:
    db_helper = request.app.db_helper
    subject_service = request.app.subject_service

    if subject := subject_service.remember_me(db_helper, subject_remember_me):
        return subject
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not remember")
