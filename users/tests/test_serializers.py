import pytest
from users.serializers import LoginSerializer, RegisterSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
class TestRegisterSerializer:

    def test_creates_user_successfully(self):
        data = {
            "email": "test@example.com",
            "password": "securepass123",
            "name": "Test User",
            "age": 22,
            "preference": "loans"
        }

        serializer = RegisterSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        user = serializer.save()

        assert user.email == data["email"]
        assert user.name == data["name"]
        assert user.check_password(data["password"])  # verifica que se encriptó

@pytest.mark.django_db
class TestLoginSerializer:

    def test_valid_login_returns_tokens(self):
        user = User.objects.create_user(
            email="login@example.com",
            name="Login Test",
            age=25,
            password="loginpass123",
            preference="investment"
        )

        data = {
            "email": "login@example.com",
            "password": "loginpass123"
        }

        serializer = LoginSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        result = serializer.validated_data

        assert "access" in result
        assert "refresh" in result
        assert result["user"]["email"] == user.email

    def test_invalid_credentials(self):
        data = {
            "email": "wrong@example.com",
            "password": "wrongpass"
        }

        serializer = LoginSerializer(data=data)
        assert not serializer.is_valid()
