from django.db import models
from users.models import User

class LearningPath(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_paths')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Learning Path #{self.id} - User: {self.user.email}"
