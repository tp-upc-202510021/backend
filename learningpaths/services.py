from learningpaths.models import LearningPath
from learningmodules.services import create_modules_from_gemini
from datetime import datetime

def create_learning_path_with_modules(user):
    learning_path = LearningPath.objects.create(
        user=user,
        created_at=datetime.now()
    )

    modules = create_modules_from_gemini(user.id, learning_path.id)

    return {
        "learning_path": {
            "id": learning_path.id,
            "user_id": learning_path.user_id,
            "created_at": learning_path.created_at.isoformat(),
        },
        "modules": modules
    }
