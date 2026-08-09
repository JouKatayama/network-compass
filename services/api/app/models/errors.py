from app.models.domain import DomainSchema


class ErrorDetailSchema(DomainSchema):
    code: str
    message: str
    request_id: str


class ErrorResponseSchema(DomainSchema):
    error: ErrorDetailSchema
