# apps/documents/urls.py
from django.urls import path
from apps.document.api.views import RAGQueryView, DocumentCreateAPIView,DocumentListAPIView

urlpatterns = [
    path("rag/", RAGQueryView.as_view(), name="rag-query"),
    path('create/', DocumentCreateAPIView.as_view(), name='documentcreate'),
    path('list/', DocumentListAPIView.as_view(), name='documentlist'),

]