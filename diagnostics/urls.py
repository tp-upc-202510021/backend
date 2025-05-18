from django.urls import path
from diagnostics.views import DiagnosticCreateView

urlpatterns = [
    path('', DiagnosticCreateView.as_view(), name='create_diagnostic'),
]
