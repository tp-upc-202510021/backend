from django.urls import path

from .views import ExchangeEventView, LoanGameAIView, RateEventView, RespondToGameView, SaveLoanGameResultView, invite_to_game_view

urlpatterns = [
    path('generate-loan-game/ai/', LoanGameAIView.as_view(), name='loan-game-ai'),
    path('rate-event/', RateEventView.as_view(), name='rate-event'),
    path('invite-to-game/', invite_to_game_view, name='invite-to-game'),
    path('respond-to-invitation/', RespondToGameView.as_view(), name='respond-to-invitation'),
    path('save-game-result/', SaveLoanGameResultView.as_view(), name='save-game-result'),
    path('apply-exchange-event/', ExchangeEventView.as_view(), name='apply-exchange-event'),
]