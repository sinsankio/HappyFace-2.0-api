from fastapi import APIRouter, Request, status, HTTPException, Body

from entity.models import AdministrativeOrganization, AuthAdmin, BasicRememberMe, Admin

router = APIRouter()


@router.post("", response_description="admin retrieval", status_code=status.HTTP_200_OK, response_model=Admin)
async def fetch_admin(request: Request, admin: AuthAdmin = Body(...)) -> dict:
    auth_service = request.app.auth_service
    db_helper = request.app.db_helper
    admin_service = request.app.admin_service

    if auth_admin := auth_service.auth_admin(db_helper, admin_service, admin):
        return auth_admin
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized request")


@router.put("/credentials", response_description="admin credential modification", status_code=status.HTTP_200_OK,
            response_model=Admin)
async def update_admin_with_credentials(request: Request, admin: AuthAdmin = Body(...), new_admin: Admin = Body(...)) \
        -> dict:
    auth_service = request.app.auth_service
    db_helper = request.app.db_helper
    admin_service = request.app.admin_service

    if auth_admin := auth_service.auth_admin(db_helper, admin_service, admin):
        if admin := admin_service.update(db_helper, auth_admin, new_admin):
            return admin
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized request")


@router.put("", response_description="admin modification", status_code=status.HTTP_200_OK, response_model=Admin)
async def update_admin(request: Request, admin: AuthAdmin = Body(...), new_admin: Admin = Body(...)) -> dict:
    auth_service = request.app.auth_service
    db_helper = request.app.db_helper
    admin_service = request.app.admin_service

    if auth_admin := auth_service.auth_admin(db_helper, admin_service, admin):
        if admin := admin_service.update(db_helper, auth_admin, new_admin, hashing=False):
            return admin
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized request")


@router.post("/orgs/all", response_description="all organization retrieval", status_code=status.HTTP_200_OK,
             response_model=list[AdministrativeOrganization])
async def fetch_organizations(request: Request, admin: AuthAdmin = Body(...)) -> list[dict]:
    auth_service = request.app.auth_service
    db_helper = request.app.db_helper
    admin_service = request.app.admin_service
    organization_service = request.app.organization_service

    if _ := auth_service.auth_admin(db_helper, admin_service, admin):
        if organizations := organization_service.retrieve_all(db_helper):
            return organizations
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="organization(s) not available")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized request")


@router.post("/remember", response_description="admin remember me", status_code=status.HTTP_200_OK, response_model=Admin)
async def remember_me(request: Request, basic_remember_me: BasicRememberMe = Body(...)) -> dict:
    db_helper = request.app.db_helper
    admin_service = request.app.admin_service

    if admin := admin_service.remember_me(db_helper, basic_remember_me):
        return admin
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not remember")
