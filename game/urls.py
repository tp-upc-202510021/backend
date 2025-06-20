from django.urls import path

from game.services import respond_to_loan_invitation
from .views import LoanGameAIView, RateEventView, invite_to_game_view

urlpatterns = [
    path('generate-loan-game/ai/', LoanGameAIView.as_view(), name='loan-game-ai'),
    path('rate-event/', RateEventView.as_view(), name='rate-event'),
    path('invite-to-game/', invite_to_game_view, name='invite-to-game'),
    path('respond-to-invitation/', respond_to_loan_invitation, name='respond-to-invitation'),
]