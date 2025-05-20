from django.urls import path
from diagnostics.views import DiagnosticCreateView, DiagnosticListView

urlpatterns = [
    path('', DiagnosticCreateView.as_view(), name='create_diagnostic'),
    path('my/', DiagnosticListView.as_view(), name='my_diagnostics'),
]
