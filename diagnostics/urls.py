from django.urls import path
from diagnostics.views import DiagnosticCreateView, DiagnosticListView, DiagnosticQuestionListView, LearningSectionListView

urlpatterns = [
    path('', DiagnosticCreateView.as_view(), name='create_diagnostic'),
    path('my/', DiagnosticListView.as_view(), name='my_diagnostics'),
    path('learning-sections/', LearningSectionListView.as_view(), name='learning_sections'),
    path('diagnostic-questions/', DiagnosticQuestionListView.as_view(), name='diagnostic_questions'),
]
