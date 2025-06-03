from django.urls import path
from .views import CreateLearningPathView, LatestLearningPathView

urlpatterns = [
    path('create/', CreateLearningPathView.as_view(), name='create_learning_path_with_modules'),
    path('latest/', LatestLearningPathView.as_view(), name='latest-learning-path'),
]