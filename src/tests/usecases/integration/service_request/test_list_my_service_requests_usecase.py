from datetime import datetime, timedelta
from uuid import uuid4
from domain.user.user_exceptions import UserNotFoundError
from domain.service_request.service_request_entity import ServiceRequest
from infrastructure.service.sqlalchemy.service_repository import ServiceRepository
from infrastructure.service_request.sqlalchemy.service_request_repository import ServiceRequestRepository
from infrastructure.user.sqlalchemy.user_repository import userRepository
from tests.conftest import make_service
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from domain.__seedwork.exceptions import ForbiddenError
from domain.service_request.service_request_repository_interface import (
    ServiceRequestRepositoryInterface,
)
from domain.user.user_repository_interface import userRepositoryInterface
from usecases.service_request.list_my_service_requests.list_my_service_requests_usecase import (
    ListMyServiceRequestsUseCase,
)
from usecases.service_request.list_my_service_requests.list_my_service_requests_dto import (
    ListMyServiceRequestsInputDTO,
)
# from models import (
#     User,
#     ServiceRequest,
# )  # Assuming you have User and ServiceRequest models defined


# BEGIN: Test Class
class TestListMyServiceRequestsUseCase:

    def test_list_service_requests_success(self,tst_db_session, make_user, make_service, seed_roles,    ):

        session = tst_db_session
        service_request_repository = ServiceRequestRepository(session=session)
        user_repository = userRepository(session=session)
        service_repository = ServiceRepository(session=session)

        client1 = make_user(
            id=uuid4(),
            name="Cliente",
            email="cliente1@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        client2 = make_user(
            id=uuid4(),
            name="Cliente",
            email="cliente2@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        
        user_repository.add_user(client1)
        user_repository.add_user(client2)

        service1 = make_service(
            id=uuid4(),
            name="DEPILAÇÃO DE CILIOS",
            description="Serviço de depilação",
        )        
        
        service2 = make_service(
            id=uuid4(),
            name="manicure em gel",
            description="Serviço de Manicure em gel",
        )        
        
        service3 = make_service(
            id=uuid4(),
            name="servico de taxy",
            description="Serviço de taxi eletreico",
        )        

        service_repository.create_service(service1)
        service_repository.create_service(service2)
        service_repository.create_service(service3)
        
        session.commit()
        

        # Add service requests for the active client
        service_request1 = ServiceRequest(
            id=uuid4(),
            client_id=client1.id,
            service_id=service1.id,
            desired_datetime=datetime.utcnow() + timedelta(days=1),
            address="123 Test St",
            created_at=datetime.utcnow() - timedelta(hours=2),
        )
        
        # Add service requests for the active client
        service_request2 = ServiceRequest(
             id=uuid4(),
            client_id=client1.id,
            service_id=service2.id,
            desired_datetime=datetime.utcnow() + timedelta(days=2),
            address="123 Test St",
            created_at=datetime.utcnow() - timedelta(hours=1),
        )

        service_request3 = ServiceRequest(
             id=uuid4(),
            client_id=client2.id,
            service_id=service3.id,
            desired_datetime=datetime.utcnow() + timedelta(days=2),
            address="123 Test St",
            created_at=datetime.utcnow() - timedelta(hours=1),
        )

        service_request_repository.create(service_request1)
        service_request_repository.create(service_request2)
        service_request_repository.create(service_request3)

        session.commit()

        use_case = ListMyServiceRequestsUseCase(
            service_request_repository= service_request_repository, 
            user_repository=user_repository
        )

        input_dto = ListMyServiceRequestsInputDTO(client_id=client1.id)
        output = use_case.execute(input_dto)

        assert len(output) == 2
        assert output[0].service_name == "Manicure Em Gel"
        assert output[0].status == "REQUESTED"
        assert output[0].service_description == "Serviço de Manicure em gel"

        assert output[1].service_name == "Depilação de Cilios"
        assert output[1].status == "REQUESTED"
        assert output[1].service_description == "Serviço de depilação"


    def test_list_service_requests_user_inactive(self,tst_db_session, make_user, make_service, seed_roles,    ):
        session = tst_db_session
        service_request_repository = ServiceRequestRepository(session=session)
        user_repository = userRepository(session=session)

        client1 = make_user(
            id=uuid4(),
            name="Cliente",
            email="cliente1@example.com",
            hashed_password="hashed_password",
            is_active=False,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"cliente"},
        )
        user_repository.add_user(client1)

        use_case = ListMyServiceRequestsUseCase(
            service_request_repository= service_request_repository, 
            user_repository=user_repository
        )

        input_dto = ListMyServiceRequestsInputDTO(client_id=client1.id)

        with pytest.raises(ForbiddenError):
            use_case.execute(input_dto)
            
    def test_list_service_requests_user_NotFound(self,tst_db_session, make_user, make_service, seed_roles,    ):
        session = tst_db_session
        service_request_repository = ServiceRequestRepository(session=session)
        user_repository = userRepository(session=session)

        use_case = ListMyServiceRequestsUseCase(
            service_request_repository= service_request_repository, 
            user_repository=user_repository
        )

        input_dto = ListMyServiceRequestsInputDTO(client_id=uuid4())

        with pytest.raises(UserNotFoundError):
            use_case.execute(input_dto)
            

    def test_list_service_requests_user_not_client(self,tst_db_session, make_user, make_service, seed_roles,    ):
        session = tst_db_session
        service_request_repository = ServiceRequestRepository(session=session)
        user_repository = userRepository(session=session)

        client1 = make_user(
            id=uuid4(),
            name="Cliente",
            email="cliente1@example.com",
            hashed_password="hashed_password",
            is_active=True,
            activation_code=None,
            activation_code_expires_at=None,
            roles={"prestador"},  # Note: not a "cliente"
        )
        user_repository.add_user(client1)

        use_case = ListMyServiceRequestsUseCase(
            service_request_repository= service_request_repository, 
            user_repository=user_repository
        )

        input_dto = ListMyServiceRequestsInputDTO(client_id=client1.id)

        with pytest.raises(ForbiddenError):
            use_case.execute(input_dto)


# END: Test Class
