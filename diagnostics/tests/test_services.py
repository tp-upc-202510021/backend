import pytest
from django.core.exceptions import ObjectDoesNotExist
from diagnostics.models import Diagnostic
from diagnostics.services import (
    create_diagnostic,
    get_diagnostics_for_user
)
from users.models import User

@pytest.mark.django_db
class TestDiagnosticServices:

    def test_create_diagnostic_with_extended_data(self):
        user = User.objects.create_user(
            email="extended@example.com",
            password="securepass",
            name="Extended User",
            age=24,
            preference="loans"
        )

        data = {
            "score": 95,
            "level": "advanced",
            "response_tone": "Tono creativo e imaginativo",
            "motivation": "Obtener 10000 soles en 2 años",
            "modules": [1, 2, 3, 4, 9, 10, 11, 12, 13, 14, 15]
        }

        diagnostic = create_diagnostic(user=user, data=data)

        assert diagnostic.user == user
        assert diagnostic.type == "loans"
        assert diagnostic.score == 95
        assert diagnostic.level == "advanced"
        assert diagnostic.response_tone == "Tono creativo e imaginativo"
        assert diagnostic.motivation == "Obtener 10000 soles en 2 años"
        assert diagnostic.modules == [1, 2, 3, 4, 9, 10, 11, 12, 13, 14, 15]

    def test_create_diagnostic_fails_if_exists(self):
        user = User.objects.create_user(
            email="duplicate@example.com",
            password="securepass",
            name="User",
            age=25,
            preference="loans"
        )

        Diagnostic.objects.create(
            user=user,
            type="loans",
            score=60,
            level="beginner"
        )

        with pytest.raises(ValueError, match="Ya existe un diagnóstico para este usuario."):
            create_diagnostic(user=user, data={  # ✅
            "score": 90,
            "level": "advanced",
            "response_tone": "Otro tono",
            "motivation": "Otra motivación",
            "modules": [1, 2]
        })

    def test_get_diagnostics_for_user_successfully(self):
        user = User.objects.create_user(
            email="hasdiag@example.com",
            password="securepass",
            name="Diag User",
            age=30,
            preference="loans"
        )

        Diagnostic.objects.create(user=user, type="loans", score=70, level="beginner")
        Diagnostic.objects.create(user=user, type="loans", score=80, level="intermediate")

        diagnostics = get_diagnostics_for_user(user)

        assert diagnostics.count() == 2
        assert all(d.user == user for d in diagnostics)

    def test_get_diagnostics_for_user_raises_if_none(self):
        user = User.objects.create_user(
            email="nodiag@example.com",
            password="securepass",
            name="NoDiag",
            age=22,
            preference="loans"
        )

        with pytest.raises(ObjectDoesNotExist):
            get_diagnostics_for_user(user)
