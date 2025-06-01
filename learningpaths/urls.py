from django.urls import path
from .views import CreateLearningPathView

urlpatterns = [
    path('create/', CreateLearningPathView.as_view(), name='create_learning_path_with_modules'),
]