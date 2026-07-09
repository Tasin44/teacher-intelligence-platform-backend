from django.urls import path
from .views import GenerateParentMessageView, SendParentMessageView, ParentMessageListView

urlpatterns = [
    path("",                          ParentMessageListView.as_view(),    name="parent-messages-list"),
    path("generate",                  GenerateParentMessageView.as_view(), name="parent-message-generate"),
    path("<int:message_id>/send",     SendParentMessageView.as_view(),     name="parent-message-send"),
]
