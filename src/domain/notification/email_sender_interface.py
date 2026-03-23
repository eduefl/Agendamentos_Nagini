from abc import ABC, abstractmethod

class EmailSenderInterface(ABC):
    @abstractmethod
    def send_activation_email(self, to_email: str, activation_code: str) -> None:
        raise NotImplementedError
