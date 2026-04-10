from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4
from domain.payment.payment_acl_gateway_interface import PaymentAclGatewayInterface
from domain.payment.payment_attempt_status import PaymentAttemptStatus
from domain.payment.payment_dto import PaymentResultDTO
_APPROVAL_THRESHOLD = Decimal("500.00")
_DEFAULT_PROVIDER = "mock-payment-provider"
class MockPaymentAclGateway(PaymentAclGatewayInterface):
    """
    Mock determinístico da ACL de Pagamento.
    Permite configurar o status forçado via construtor para facilitar o controle
    em testes. Se não configurado, aplica regra determinística por valor:
    - APPROVED quando amount < 500.00
    - REFUSED quando amount >= 500.00
    Nunca usa aleatoriedade.
    """
    def __init__(
        self,
        forced_status: Optional[PaymentAttemptStatus] = None,
        provider: str = _DEFAULT_PROVIDER,
    ):
        self._forced_status = forced_status
        self._provider = provider
    def process_payment(
        self,
        external_reference: str,
        amount: Decimal,
        payer_id: UUID,
        service_request_id: UUID,
        requested_at: datetime,
    ) -> PaymentResultDTO:
        if self._forced_status is not None:
            status = self._forced_status
        else:
            status = (
                PaymentAttemptStatus.APPROVED
                if amount < _APPROVAL_THRESHOLD
                else PaymentAttemptStatus.REFUSED
            )
        refusal_reason = None
        provider_message = None
        if status == PaymentAttemptStatus.APPROVED:
            provider_message = "Pagamento aprovado pelo mock"
        else:
            refusal_reason = "Valor acima do limite permitido pelo mock"
            provider_message = "Pagamento recusado pelo mock"
        return PaymentResultDTO(
            provider=self._provider,
            external_reference=external_reference,
            status=status,
            processed_at=datetime.utcnow(),
            refusal_reason=refusal_reason,
            provider_message=provider_message,
        )