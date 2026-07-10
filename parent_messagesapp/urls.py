from django.urls import path
from .views import GenerateParentMessageView, SendParentMessageView, ParentMessageListView, DownloadParentMessagePDFView, ParentMessageDetailView

urlpatterns = [
    path("",                          ParentMessageListView.as_view(),    name="parent-messages-list"),
    path("generate",                  GenerateParentMessageView.as_view(), name="parent-message-generate"),
    path("<int:message_id>/",         ParentMessageDetailView.as_view(),   name="parent-message-detail"),
    path("<int:message_id>/send",     SendParentMessageView.as_view(),     name="parent-message-send"),
    path("<int:message_id>/download-pdf", DownloadParentMessagePDFView.as_view(), name="parent-message-download-pdf"),
]
