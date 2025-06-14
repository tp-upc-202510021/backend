from django.db import models
from learningpaths.models import LearningPath

class LearningModule(models.Model):
    learning_path = models.ForeignKey(LearningPath, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField()
    level = models.CharField(max_length=50)
    order_index = models.PositiveIntegerField()
    content = models.JSONField(null=True, blank=True) 
    is_blocked = models.BooleanField(default=False)
    def __str__(self):
        return self.title
