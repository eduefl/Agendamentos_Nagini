from domain.__seedwork.exceptions import DomainError
class EmailDeliveryError(DomainError):
    def __init__(self , message: str = "Failed to send email notification"):
        super().__init__(message)
