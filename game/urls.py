from django.urls import path
from .views import LoanGameAIView

urlpatterns = [
    path('generate-loan-game/ai/', LoanGameAIView.as_view(), name='loan-game-ai'),
]