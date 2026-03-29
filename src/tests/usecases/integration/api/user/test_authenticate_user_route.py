from uuid import uuid4
from infrastructure.security.factories.make_token_service import make_token_service
from infrastructure.security.passlib_password_hasher import PasslibPasswordHasher
from infrastructure.user.sqlalchemy.user_repository import userRepository
from fastapi.testclient import TestClient

class TestAuthenticateUserRoute:
	def test_login_success(self, client: TestClient, tst_db_session, make_user, seed_roles):
		session = tst_db_session
		user_repoitory = userRepository(session=session)
		hasher = PasslibPasswordHasher()
		token_service = make_token_service()

		user_id = uuid4()
		email_in = "john@example.com"
		password = "Abc12345"
		hash_pass = hasher.hash(password)

		user = make_user(
			id=user_id,
			name="John Doe",
			email=email_in,
			hashed_password=hash_pass,
			is_active=True,
			activation_code=None,
			activation_code_expires_at=None,
			roles={"cliente"},
		)
		user_repoitory.add_user(user=user)
		
		valid_user = {
			"username": email_in,
			"password": password  
		}
		
		response = client.post("/users/login/", data=valid_user)
		
		assert response.status_code == 200
		body = response.json()
		assert "token_type" in body  
		assert body["token_type"] == "bearer"
		assert "access_token" in body
		assert isinstance(body["access_token"], str)
		payload = token_service.decode_token(body["access_token"])
		assert payload.sub == user_id
		assert payload.email == email_in
		assert payload.roles == sorted(map(str, user.roles))


	def test_login_inactive_user(self, client: TestClient, tst_db_session, make_user, seed_roles):
		session = tst_db_session
		user_repoitory = userRepository(session=session)
		hasher = PasslibPasswordHasher()

		user_id = uuid4()
		email_in = "john@example.com"
		password = "Abc12345"
		hash_pass = hasher.hash(password)

		user = make_user(
			id=user_id,
			name="John Doe",
			email=email_in,
			hashed_password=hash_pass,
			is_active=False,
			activation_code=None,
			activation_code_expires_at=None,
			roles={"cliente"},
		)
		user_repoitory.add_user(user=user)
		
		valid_user = {
			"username": email_in,
			"password": password  
		}
		
		response = client.post("/users/login/", data=valid_user)
		
		assert response.status_code == 401  # Unauthorized
		body = response.json()
		assert "detail" in body
		assert "invalid email or password" in body["detail"].lower()


	def test_login_failure_invalid_credentials(self, client: TestClient, tst_db_session, make_user, seed_roles):
		session = tst_db_session
		user_repoitory = userRepository(session=session)
		hasher = PasslibPasswordHasher()

		user_id = uuid4()
		email_in = "john@example.com"
		password = "Wrong Password"
		hash_pass = hasher.hash(password)

		user = make_user(
			id=user_id,
			name="John Doe",
			email=email_in,
			hashed_password=hash_pass,
			is_active=True,
			activation_code=None,
			activation_code_expires_at=None,
			roles={"cliente"},
		)
		user_repoitory.add_user(user=user)
		
		valid_user = {
			"username": email_in,
			"password": "Wrong password"  
		}
		
		response = client.post("/users/login/", data=valid_user)
		
		assert response.status_code == 401  # Unauthorized
		body = response.json()
		assert "detail" in body
		assert "invalid email or password" in body["detail"].lower()

	def test_login_failure_user_not_found(self, client: TestClient, tst_db_session, make_user, seed_roles):
		non_existent_user = {
			"username": "nonexistent@example.com",
			"password": "any_password"
		}
		
		response = client.post("/users/login/", data=non_existent_user)
		assert response.status_code == 401  # Unauthorized
		body = response.json()
		assert "detail" in body
		assert "invalid email or password" in body["detail"].lower()
