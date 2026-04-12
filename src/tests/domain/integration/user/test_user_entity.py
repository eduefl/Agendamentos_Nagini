from datetime import datetime, timedelta

class TestUserWithactivation:
    def test_user_is_inactive_by_default(self,make_user):
        user = make_user()
        assert user.is_active is False


    def test_user_activation_lifecycle(self, make_user):
        user = make_user()

        assert user.is_active is False
        assert user.activation_code is None
        assert user.activation_code_expires_at is None

        expires_at = datetime.now() + timedelta(minutes=15)
        user.set_activation_code("abc12345", expires_at)

        assert user.activation_code == "abc12345"
        assert user.activation_code_expires_at == expires_at

        user.activate()

        assert user.is_active is True
        assert user.activation_code is None
        assert user.activation_code_expires_at is None