from django.shortcuts import render
import mimetypes
from django.db.models import Q
from django.core.paginator import Paginator
from requests.auth import HTTPBasicAuth
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework import viewsets, permissions, status
#from .models import _
#from .serializers import _
from django.views.decorators.http import require_http_methods
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User 
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseServerError
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.contrib.auth import login, authenticate,get_user_model
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist


class MyLoginView(LoginView):
    def form_valid(self, form):
        login(self.request, form.get_user())
        user = form.get_user()
        if not user:
            return redirect("myApplicationManager:register")
        return redirect("myApplicationManager:homepage") 
    
    def form_invalid(self, form):
        username = self.request.POST.get('username')
        password = self.request.POST.get('password')

        User = get_user_model()
        try:
            user = User.objects.get(username=username)
            if user.check_password(password) and not user.is_active:
                form.add_error(None, "Your account is pending admin approval. Please wait for confirmation before logging in.")
        except User.DoesNotExist:
            pass  # normal invalid credentials case

        return super().form_invalid(form)


def homepage(request):
    return render(request, "homePage.html", {"user":request.user})
    

def register(request):
    from django.contrib.auth.forms import UserCreationForm    
    
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()     
            login(request, user)        
            return redirect("myApplicationManager:homepage")      
    else:
        form = UserCreationForm()
    return render(request, "register.html", {"form": form})