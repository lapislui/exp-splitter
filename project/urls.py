from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def home(request):
    return render(request, 'home.html')

@login_required
def add_member(request):
    return render(request, 'add_member.html')

@login_required
def add_expense(request):
    return render(request, 'add_expense.html')

@login_required
def report(request):
    return render(request, 'report.html')

urlpatterns = [
    path('', home, name='home'),
    path('add-member/', add_member, name='add-member'),
    path('add-expense/', add_expense, name='add-expense'),
    path('report/', report, name='report'),
    path('admin/', admin.site.urls),
    path('api/', include('splitter.urls')),
]
