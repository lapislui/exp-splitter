from django.urls import path
from .views import (
    GroupListCreate, AddMemberView, ExpenseListCreate,
    create_user, get_group_members, group_report, download_report_pdf,
    user_login, user_register, user_logout
)

urlpatterns = [
    path('groups/', GroupListCreate.as_view(), name='group-list'),
    path('groups/create/', GroupListCreate.as_view(), name='group-create'),
    path('users/create/', create_user, name='create-user'),
    path('groups/<int:group_id>/members/list/', get_group_members, name='group-members'),
    path('groups/<int:group_id>/members/', AddMemberView.as_view(), name='add-member'),
    path('groups/<int:group_id>/expenses/', ExpenseListCreate.as_view(), name='expense-list'),
    path('groups/<int:group_id>/report/', group_report, name='group-report'),
    path('groups/<int:group_id>/report/pdf/', download_report_pdf, name='download-report-pdf'),
    path('login/', user_login, name='login'),
    path('register/', user_register, name='register'),
    path('logout/', user_logout, name='logout'),
]