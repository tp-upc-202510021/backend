from learningpaths.models import LearningPath
from learningmodules.services import create_modules_from_gemini
from learningmodules.models import LearningModule

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

def get_latest_learning_path_with_modules(user_id):
    latest_path = LearningPath.objects.filter(user_id=user_id).order_by('-created_at').first()
    if not latest_path:
        return None

    modules = LearningModule.objects.filter(learning_path=latest_path).order_by('order_index')
    return {
        "learning_path_id": latest_path.id,
        "user_id": latest_path.user_id,
        "created_at": latest_path.created_at.isoformat(),
        "modules": [
            {
                "title": m.title,
                "description": m.description,
                "level": m.level,
                "order_index": m.order_index,
                "is_blocked": m.is_blocked,
            }
            for m in modules
        ]
    }
