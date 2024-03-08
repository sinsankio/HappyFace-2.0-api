from entity.models import AuthAdmin, AuthOrganization, AuthSubject
from helper.database.mongodb.db_helper import DbHelper
from service.admin_service import AdminService
from service.organization_service import OrganizationService
from service.subject_service import SubjectService


class AuthService:
    def auth_admin(self, db_helper: DbHelper, admin_service: AdminService,
                   admin: AuthAdmin) -> dict | None:
        if auth_admin := admin_service.authenticate(db_helper, admin):
            return auth_admin

    def auth_organization(self, db_helper: DbHelper, organization_service: OrganizationService,
                          organization: AuthOrganization) -> dict | None:
        if auth_organization := organization_service.authenticate(db_helper, organization):
            return auth_organization

    def auth_subject(self, db_helper: DbHelper, subject_service: SubjectService, subject: AuthSubject) -> dict | None:
        if auth_org_subject := subject_service.authenticate(db_helper, subject):
            return auth_org_subject
