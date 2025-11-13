from django.urls import path
from .views import (
    GroupListCreate, AddMemberView, ExpenseListCreate,
    create_user, get_group_members, group_report, download_report_pdf
)

urlpatterns = [
    path('groups/', GroupListCreate.as_view(), name='group-list'),
    path('groups/<int:group_id>/members/', AddMemberView.as_view(), name='add-member'),
    path('groups/<int:group_id>/expenses/', ExpenseListCreate.as_view(), name='expense-list'),
    path('groups/<int:group_id>/report/', group_report, name='group-report'),
    path('groups/<int:group_id>/report/pdf/', download_report_pdf, name='download-report-pdf'),
    path('groups/<int:group_id>/members/list/', get_group_members, name='group-members'),
    path('users/create/', create_user, name='create-user'),
]