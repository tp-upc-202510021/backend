from django.urls import path
from .views import GenerateQuizView, LatestQuizView

urlpatterns = [
    path('generate/<int:module_id>/', GenerateQuizView.as_view(), name='generate-quiz'),
    path('latest/<int:module_id>/', LatestQuizView.as_view(), name='latest-quiz'),
]
