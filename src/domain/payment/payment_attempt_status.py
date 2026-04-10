from enum import Enum


class PaymentAttemptStatus(str, Enum):
    REQUESTED = "REQUESTED"
    PROCESSING = "PROCESSING"
    APPROVED = "APPROVED"
    REFUSED = "REFUSED"