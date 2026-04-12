
import logging
from datetime import datetime
from uuid import uuid4

from domain.payment.payment_acl_gateway_interface import PaymentAclGatewayInterface
from domain.payment.payment_attempt_repository_interface import (
    PaymentAttemptRepositoryInterface,
)
from domain.payment.payment_attempt_status import PaymentAttemptStatus
from domain.service_request.service_request_entity import ServiceRequestStatus
from domain.service_request.service_request_exceptions import (
    ClientNotAllowedToConfirmPaymentError,
    ServiceRequestAlreadyCompletedError,
    ServiceRequestNotFoundError,
    ServiceRequestNotAwaitingPaymentError,
    ServiceRequestPaymentAlreadyProcessingError,
    ServiceRequestPaymentAmountInvalidError,
    ServiceRequestPaymentNotRequestedError,
    PaymentGatewayTechnicalFailureError,
)
from domain.service_request.service_request_repository_interface import (
    ServiceRequestRepositoryInterface,
)
from usecases.service_request.apply_payment_result.apply_payment_result_usecase import (
    ApplyPaymentResultUseCase,
)
from usecases.service_request.confirm_payment.confirm_payment_dto import (
    ConfirmPaymentInputDTO,
    ConfirmPaymentOutputDTO,
)

logger = logging.getLogger(__name__)


class ConfirmPaymentUseCase:
    def __init__(
        self,
        service_request_repository: ServiceRequestRepositoryInterface,
        payment_attempt_repository: PaymentAttemptRepositoryInterface,
        payment_acl_gateway: PaymentAclGatewayInterface,
        apply_payment_result_usecase: ApplyPaymentResultUseCase,
    ):
        self._service_request_repository = service_request_repository
        self._payment_attempt_repository = payment_attempt_repository
        self._payment_acl_gateway = payment_acl_gateway
        self._apply_payment_result_usecase = apply_payment_result_usecase

    def execute(
        self,
        input_dto: ConfirmPaymentInputDTO,
    ) -> ConfirmPaymentOutputDTO:
        # 1. Carregar o ServiceRequest
        service_request = self._service_request_repository.find_by_id(
            input_dto.service_request_id
        )
        if service_request is None:
            raise ServiceRequestNotFoundError()

        # 2. Validar autorização: o usuário autenticado deve ser o client_id
        self._validate_actor(service_request, input_dto.authenticated_user_id)

        # 3. Validar estado do ServiceRequest
        self._validate_state(service_request)

        # 4. Localizar a PaymentAttempt corrente
        attempt = self._load_current_attempt(input_dto.service_request_id)

        # 5. Capturar timestamp único para toda a operação
        now = datetime.utcnow()

        # 6. Persistir transição atômica:
        #    - ServiceRequest: AWAITING_PAYMENT -> PAYMENT_PROCESSING
        #    - PaymentAttempt: REQUESTED -> PROCESSING
        #    Ambas em um único commit; ACL só é chamada após a persistência.
        updated = self._service_request_repository.start_payment_processing_and_mark_attempt_if_awaiting_payment(
            service_request_id=input_dto.service_request_id,
            client_id=input_dto.authenticated_user_id,
            attempt_id=attempt.id,
            now=now,
        )

        if updated is None:
            # Update condicional falhou — re-ler para classificar o erro
            current = self._service_request_repository.find_by_id(
                input_dto.service_request_id
            )
            if current is None:
                raise ServiceRequestNotFoundError()
            if current.client_id != input_dto.authenticated_user_id:
                raise ClientNotAllowedToConfirmPaymentError()
            if current.status == ServiceRequestStatus.COMPLETED.value:
                raise ServiceRequestAlreadyCompletedError()
            if current.status == ServiceRequestStatus.PAYMENT_PROCESSING.value:
                raise ServiceRequestPaymentAlreadyProcessingError()
            raise ServiceRequestNotAwaitingPaymentError()

        # 7. Chamar a ACL de pagamento (banco já reflete PAYMENT_PROCESSING)
        #    Falha técnica da ACL mantém o estado em PAYMENT_PROCESSING e
        #    propaga PaymentGatewayTechnicalFailureError -> 502/503 na camada HTTP.
        external_reference = str(uuid4())
        payment_result = self._call_payment_acl(
            external_reference=external_reference,
            updated=updated,
            attempt=attempt,
        )

        # 8. Delegar o resultado para ApplyPaymentResultUseCase
        self._apply_payment_result_usecase.execute(
            service_request_id=updated.id,
            attempt_id=attempt.id,
            payment_result=payment_result,
            now=now,
        )

        # 9. Re-ler o ServiceRequest para obter o estado final (COMPLETED ou AWAITING_PAYMENT)
        final = self._service_request_repository.find_by_id(updated.id) or updated

        # 10. Devolver resposta com estado final para a API
        return ConfirmPaymentOutputDTO(
            service_request_id=final.id,
            status=final.status,
            payment_processing_started_at=updated.payment_processing_started_at,
            payment_reference=payment_result.external_reference,
        )

    def _validate_actor(self, service_request, authenticated_user_id) -> None:
        if service_request.client_id != authenticated_user_id:
            raise ClientNotAllowedToConfirmPaymentError()

    def _validate_state(self, service_request) -> None:
        if service_request.status == ServiceRequestStatus.COMPLETED.value:
            raise ServiceRequestAlreadyCompletedError()

        if service_request.status == ServiceRequestStatus.PAYMENT_PROCESSING.value:
            raise ServiceRequestPaymentAlreadyProcessingError()

        if service_request.status != ServiceRequestStatus.AWAITING_PAYMENT.value:
            raise ServiceRequestNotAwaitingPaymentError()

        if service_request.service_finished_at is None:
            raise ServiceRequestNotAwaitingPaymentError()

        if service_request.payment_requested_at is None:
            raise ServiceRequestNotAwaitingPaymentError()

        if (
            service_request.payment_amount is None
            or service_request.payment_amount <= 0
        ):
            raise ServiceRequestPaymentAmountInvalidError()

    def _load_current_attempt(self, service_request_id):
        attempt = self._payment_attempt_repository.find_latest_by_service_request_id(
            service_request_id
        )
        if attempt is None or attempt.status != PaymentAttemptStatus.REQUESTED.value:
            raise ServiceRequestPaymentNotRequestedError()
        return attempt

    def _call_payment_acl(self, external_reference, updated, attempt):
        try:
            return self._payment_acl_gateway.process_payment(
                external_reference=external_reference,
                amount=updated.payment_amount,
                payer_id=updated.client_id,
                service_request_id=updated.id,
                requested_at=updated.payment_requested_at,
            )
        except Exception as exc:
            logger.exception(
                "Falha técnica na ACL de pagamento service_request_id=%s. "
                "Estado permanece PAYMENT_PROCESSING.",
                updated.id,
            )
            raise PaymentGatewayTechnicalFailureError(
                f"Falha técnica no gateway de pagamento: {exc}"
            ) from exc