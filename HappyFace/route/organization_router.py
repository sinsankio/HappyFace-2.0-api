from fastapi import APIRouter, Body, Request, HTTPException, status, Query

from entity.models import Organization, Subject, WorkEmotionEntry, AuthOrganization, BasicRememberMe

router = APIRouter()


@router.post("/new", response_description="organization registration", status_code=status.HTTP_200_OK,
             response_model=Organization)
async def register_organization(request: Request, organization: Organization = Body(...)) -> dict:
    db_helper = request.app.db_helper
    organization_service = request.app.organization_service

    if registered_organization := organization_service.register(db_helper, organization):
        return registered_organization
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="organization registration failed")


@router.post("/subjects/new", response_description="subject registration", status_code=status.HTTP_200_OK,
             response_model=list[Subject])
async def register_subjects(request: Request, organization: AuthOrganization = Body(...),
                            subjects: list[Subject] = Body(...)) -> list[dict]:
    db_helper = request.app.db_helper
    auth_service = request.app.auth_service
    subject_service = request.app.subject_service
    organization_service = request.app.organization_service

    if auth_organization := auth_service.auth_organization(db_helper, organization_service, organization):
        if updated_subjects := subject_service.register_all(db_helper, organization_service, auth_organization, subjects):
            return updated_subjects
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="subject(s) registration failed")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized request")


@router.post("", response_description="organization retrieval", status_code=status.HTTP_200_OK,
             response_model=Organization)
async def fetch_organization(request: Request, organization: AuthOrganization = Body(...)) -> dict:
    db_helper = request.app.db_helper
    organization_service = request.app.organization_service
    auth_service = request.app.auth_service

    if auth_organization := auth_service.auth_organization(db_helper, organization_service, organization):
        return auth_organization
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized request")


@router.post("/subjects/all", response_description="all subject retrieval", status_code=status.HTTP_200_OK,
             response_model=list[Subject])
async def fetch_subjects(request: Request, organization: AuthOrganization = Body(...)) -> list[dict]:
    db_helper = request.app.db_helper
    auth_service = request.app.auth_service
    subject_service = request.app.subject_service
    organization_service = request.app.organization_service

    if auth_organization := auth_service.auth_organization(db_helper, organization_service, organization):
        if subjects := subject_service.retrieve_all(auth_organization):
            return subjects
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="subject(s) not available")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized request")


@router.put("", response_description="organization modification", status_code=status.HTTP_200_OK,
            response_model=Organization)
async def update_organization(request: Request, organization: AuthOrganization = Body(...),
                              new_organization: Organization = Body(...)) -> dict:
    db_helper = request.app.db_helper
    auth_service = request.app.auth_service
    organization_service = request.app.organization_service

    if auth_organization := auth_service.auth_organization(db_helper, organization_service, organization):
        if updated_organization := organization_service.update(db_helper, auth_organization, new_organization, hashing=False):
            return updated_organization
        raise HTTPException(status_code=status.HTTP_304_NOT_MODIFIED, detail="organization modification failed")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized request")


@router.put("/credentials", response_description="organization credential modification", status_code=status.HTTP_200_OK,
            response_model=Organization)
async def update_organization_with_credentials(request: Request, organization: AuthOrganization = Body(...),
                                               new_organization: Organization = Body(...)) -> dict:
    db_helper = request.app.db_helper
    auth_service = request.app.auth_service
    organization_service = request.app.organization_service

    if auth_organization := auth_service.auth_organization(db_helper, organization_service, organization):
        if updated_organization := organization_service.update(db_helper, auth_organization, new_organization):
            return updated_organization
        raise HTTPException(status_code=status.HTTP_304_NOT_MODIFIED, detail="organization modification failed")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized request")


@router.delete("", response_description="organization deletion", status_code=status.HTTP_200_OK)
async def delete_organization(request: Request, organization: AuthOrganization = Body(...)) -> int:
    db_helper = request.app.db_helper
    auth_service = request.app.auth_service
    organization_service = request.app.organization_service

    if auth_organization := auth_service.auth_organization(db_helper, organization_service, organization):
        if organization_service.delete(db_helper, auth_organization):
            return status.HTTP_200_OK
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="organization deletion failed")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized request")


@router.delete("/subjects", response_description="subject deletion", status_code=status.HTTP_200_OK)
async def delete_subject(request: Request, organization: AuthOrganization = Body(...),
                         sub_id: str = Query(..., description="subject id")) -> int:
    db_helper = request.app.db_helper
    crypto_helper = request.app.crypto_helper
    auth_service = request.app.auth_service
    subject_service = request.app.subject_service
    organization_service = request.app.organization_service
    sub_id = crypto_helper.decrypt(sub_id)

    if auth_organization := auth_service.auth_organization(db_helper, organization_service, organization):
        if subject_service.delete(db_helper, organization_service, auth_organization, sub_id):
            return status.HTTP_200_OK
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="organization subject deletion failed")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized request")


@router.post("/emotions", response_description="emotion engagement retrieval", status_code=status.HTTP_200_OK)
async def fetch_emotion_engagement(request: Request, organization: AuthOrganization = Body(...),
                                   hours: int = Query(None, description="hours before"),
                                   weeks: int = Query(None, description="weeks before"),
                                   months: int = Query(None, description="months before"),
                                   years: int = Query(None, description="years before")) -> dict | None:
    db_helper = request.app.db_helper
    auth_service = request.app.auth_service
    organization_service = request.app.organization_service

    if auth_organization := auth_service.auth_organization(db_helper, organization_service, organization):
        if emotional_engagement := organization_service.retrieve_emotion_engagement(db_helper, auth_organization["_id"],
                                                                                    hours=hours, weeks=weeks,
                                                                                    months=months, years=years):
            return emotional_engagement
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="organization emotional engagement not available")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized request")


@router.put("/emotions", response_description="work emotion entry submission", status_code=status.HTTP_200_OK,
            response_model=Organization)
async def upload_work_emotion_entries(request: Request, org_key=Query(..., description="organization key"),
                                      work_emotion_entries: list[WorkEmotionEntry] = Body(...)):
    db_helper = request.app.db_helper
    organization_service = request.app.organization_service

    if organization := organization_service.insert_work_emotion_entries(db_helper, org_key, work_emotion_entries):
        return organization
    raise HTTPException(status_code=status.HTTP_304_NOT_MODIFIED, detail="work emotion entry updation failed")


@router.post("/consultation", response_description="setup consultations on work entry submission",
             status_code=status.HTTP_200_OK)
async def setup_consultancy_services_on_work_emotion_entries(request: Request,
                                                             org_key=Query(..., description="organization key"),
                                                             work_emotion_entries: list[WorkEmotionEntry] = Body(
                                                                 ...)) -> int:
    db_helper = request.app.db_helper
    organization_service = request.app.organization_service

    if organization_service.init_consultancy_services_on_work_emotion_entry_submission(
            db_helper, org_key, work_emotion_entries
    ):
        return status.HTTP_200_OK
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="consultation setup failed")


@router.post("/remember", response_description="organization remember me", status_code=status.HTTP_200_OK,
             response_model=Organization)
async def remember_me(request: Request, basic_remember_me: BasicRememberMe = Body(...)) -> list[dict]:
    db_helper = request.app.db_helper
    organization_service = request.app.organization_service

    if organization := organization_service.remember_me(db_helper, basic_remember_me):
        return organization
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not remember")
