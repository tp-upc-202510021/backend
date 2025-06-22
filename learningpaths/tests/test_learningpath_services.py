import pytest
from unittest.mock import patch
from learningpaths.models import LearningPath
from learningpaths.services import (
    create_learning_path_with_modules,
    get_latest_learning_path_with_modules
)
from users.models import User
from learningmodules.models import LearningModule


@pytest.mark.django_db
class TestLearningPathServices:

    @patch("learningpaths.services.create_learning_modules")
    def test_create_learning_path_with_modules(self, mock_create_modules):
        mock_create_modules.return_value = [
            {"id": 1, "title": "Módulo 1"},
            {"id": 2, "title": "Módulo 2"},
        ]

        user = User.objects.create_user(
            email="userlp@example.com",
            password="pass123",
            name="User LP",
            age=23,
            preference="loans"
        )

        result = create_learning_path_with_modules(user)

        assert "learning_path" in result
        assert "modules" in result
        assert len(result["modules"]) == 2

        path = LearningPath.objects.get(user=user)
        assert path.id == result["learning_path"]["id"]

    @patch("learningpaths.services.create_learning_modules")
    def test_create_learning_path_fails_if_exists(self, mock_create_modules):
        user = User.objects.create_user(
            email="duplicate_lp@example.com",
            password="pass123",
            name="User",
            age=24,
            preference="loans"
        )

        LearningPath.objects.create(user=user)

        with pytest.raises(ValueError, match="Ya existe un learning path para este usuario."):
            create_learning_path_with_modules(user)

    def test_get_latest_learning_path_with_modules_returns_data(self):
        user = User.objects.create_user(
            email="pathuser@example.com",
            password="pass123",
            name="User",
            age=22,
            preference="loans"
        )

        path = LearningPath.objects.create(user=user)
        module1 = LearningModule.objects.create(
            learning_path=path,
            title="Modulo A",
            description="Desc A",
            level="beginner",
            order_index=1
        )
        module2 = LearningModule.objects.create(
            learning_path=path,
            title="Modulo B",
            description="Desc B",
            level="beginner",
            order_index=2
        )

        result = get_latest_learning_path_with_modules(user.id)

        assert result["learning_path_id"] == path.id
        assert len(result["modules"]) == 2
        assert result["modules"][0]["title"] == "Modulo A"

    def test_get_latest_learning_path_with_modules_returns_none(self):
        user = User.objects.create_user(
            email="noresult@example.com",
            password="pass123",
            name="No LP",
            age=20,
            preference="investments"
        )

        result = get_latest_learning_path_with_modules(user.id)
        assert result is None
