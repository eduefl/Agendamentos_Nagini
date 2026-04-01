from domain.__seedwork.exceptions import ValidationError, NotFoundError


class InvalidServiceRequestDateError(ValidationError):
    def __init__(self):
        super().__init__("Desired datetime must be in the future")


class ServiceRequestNotFoundError(NotFoundError):
    def __init__(self):
        super().__init__("Service request not found")
