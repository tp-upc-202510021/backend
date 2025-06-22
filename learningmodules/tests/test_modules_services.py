import pytest
from unittest.mock import patch, MagicMock
from django.core.exceptions import ObjectDoesNotExist
from learningmodules.models import LearningModule
from learningpaths.models import LearningPath
from diagnostics.models import Diagnostic, LearningSection
from users.models import User
from learningmodules.services import (
    create_learning_modules,
    get_learning_module_by_id,
    generate_module_content
)

@pytest.mark.django_db
class TestLearningModuleServices:

    def test_get_learning_module_by_id_success(self):
        user = User.objects.create_user(
            email="moduser@example.com",
            password="pass123",
            name="Mod User",
            age=20,
            preference="loans"
        )
        path = LearningPath.objects.create(user=user)
        module = LearningModule.objects.create(
            learning_path=path,
            title="Título",
            description="Descripción",
            level="beginner",
            order_index=1,
            is_blocked=False,
            is_approved=True,
            content={"pages": []}
        )

        result = get_learning_module_by_id(module.id)
        assert result["id"] == module.id
        assert result["title"] == "Título"
        assert result["is_approved"] is True

    def test_get_learning_module_by_id_not_found(self):
        with pytest.raises(ValueError, match="No se encontró ningún módulo con el ID"):
            get_learning_module_by_id(999)

    def test_create_learning_modules_success(self):
        user = User.objects.create_user(
            email="genmod@example.com",
            password="pass123",
            name="Mod",
            age=22,
            preference="loans"
        )
        path = LearningPath.objects.create(user=user)
        Diagnostic.objects.create(user=user, type="loans", score=90, level="advanced", modules=[1])
        LearningSection.objects.create(id=1, title="Intro a préstamos", description="Teoría básica", preference="loans", learning_index=1)

        result = create_learning_modules(user_id=user.id, learning_path_id=path.id)
        assert len(result) >= 1
        assert result[0]["title"] == "Intro a préstamos"

    def test_create_learning_modules_raises_if_path_has_modules(self):
        user = User.objects.create_user(
            email="duppath@example.com",
            password="pass123",
            name="User",
            age=22,
            preference="loans"
        )
        path = LearningPath.objects.create(user=user)
        LearningModule.objects.create(
            learning_path=path,
            title="Mod existente",
            description="...",
            level="beginner",
            order_index=1
        )

        with pytest.raises(ValueError, match="ya han sido creados"):
            create_learning_modules(user.id, path.id)

    @patch("learningmodules.services.client.models.generate_content")
    def test_generate_module_content_success(self, mock_gemini):
        user = User.objects.create_user(
            email="gemini@example.com",
            password="pass123",
            name="Gemini",
            age=20,
            preference="loans"
        )
        path = LearningPath.objects.create(user=user)
        Diagnostic.objects.create(
            user=user,
            type="loans",
            score=80,
            level="intermediate",
            response_tone="Motivador",
            motivation="Tener estabilidad financiera",
            modules=[1]
        )
        module = LearningModule.objects.create(
            learning_path=path,
            title="Módulo 1",
            description="Contenido",
            level="intermediate",
            order_index=1
        )

        fake_response = MagicMock()
        fake_response.text = '''
        {
            "pages": [
                {"type": "informative", "content": "# Intro\\nTexto..."},
                {"type": "practical", "content": "## Ejemplo\\nCaso..."},
                {"type": "video", "content": "https://youtube.com/watch?v=abc123"}
            ]
        }
        '''
        mock_gemini.return_value = fake_response

        result = generate_module_content(user_id=user.id, module_id=module.id)
        assert result["module_id"] == module.id
        assert "pages" in result["content"]
