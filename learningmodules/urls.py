from django.urls import path
from learningmodules.views import GenerateModuleContentView

urlpatterns = [
    path('generate-content/', GenerateModuleContentView.as_view(), name='generate-module-content'),
]
