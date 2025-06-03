from django.urls import path
from learningmodules.views import GenerateModuleContentView, GetLearningModuleView

urlpatterns = [
    path('generate-content/', GenerateModuleContentView.as_view(), name='generate-module-content'),
    path('modules/<int:module_id>/', GetLearningModuleView.as_view(), name='get_learning_module'),
]
