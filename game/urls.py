from django.urls import path
from .views import LoanGameAIView, RateEventView

urlpatterns = [
    path('generate-loan-game/ai/', LoanGameAIView.as_view(), name='loan-game-ai'),
    path('rate-event/', RateEventView.as_view(), name='rate-event'),
]