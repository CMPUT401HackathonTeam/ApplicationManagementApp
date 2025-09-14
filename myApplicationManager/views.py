from django.shortcuts import render
import mimetypes
from django.db.models import Q
from django.core.paginator import Paginator
from requests.auth import HTTPBasicAuth
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework import viewsets, permissions, status
from .models import JobApplication, Profile, JobsToApply, Resume
from .serializers import JobApplicationSerializer, ResumeSerializer
from django.views.decorators.http import require_http_methods
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User 
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseServerError, JsonResponse
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.contrib.auth import login, authenticate,get_user_model
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt
import json


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

# Resume View
@login_required
def view_resumes(request):
    """Render the Resumes page (templates/resumes.html)."""
    return render(request, 'resumes.html')

class ResumeViewSet(viewsets.ModelViewSet):
    """
    CRUD for Resume with nested children handled by ResumeSerializer.
    - Only returns the current user's resumes.
    - Creates with the current user's Profile.
    - Enforces ownership on update/delete.
    - Uses UUID 'resumeID' as the lookup field.
    - Respects soft delete by filtering is_deleted=False and calling instance.delete().
    """
    serializer_class = ResumeSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'resumeID'

    def _get_profile(self):
        user = self.request.user
        profile, _ = Profile.objects.get_or_create(
            email=user.email,
            defaults={
                'firstName': getattr(user, 'first_name', '') or '',
                'lastName': getattr(user, 'last_name', '') or '',
            }
        )
        return profile

    def get_queryset(self):
        profile = self._get_profile()
        # If your BaseModel has is_deleted, keep it hidden from normal queries
        return Resume.objects.filter(userID=profile, is_deleted=False).order_by('-uploadDate')

    def perform_create(self, serializer):
        serializer.save(userID=self._get_profile())

    def perform_update(self, serializer):
        if serializer.instance.userID != self._get_profile():
            raise PermissionDenied("You don't have permission to modify this resume.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.userID != self._get_profile():
            raise PermissionDenied("You don't have permission to delete this resume.")
        # Soft delete via your BaseModel.delete() override
        instance.delete()


# US 5.1: View all applications
@login_required
def view_applications(request):
    """US 5.1: As a user I want to be able to view all my applications"""
    try:
        # Get or create user profile
        profile, created = Profile.objects.get_or_create(
            email=request.user.email,
            defaults={
                'firstName': request.user.first_name or '',
                'lastName': request.user.last_name or '',
            }
        )
        
        # Get all applications for this user
        applications = JobApplication.objects.filter(profileID=profile).order_by('-id')
        
        # Count applications by status
        status_counts = {
            'APPLIED': applications.filter(status='APPLIED').count(),
            'INTERVIEW': applications.filter(status='INTERVIEW').count(),
            'ACCEPTED': applications.filter(status='ACCEPTED').count(),
            'REJECTED': applications.filter(status='REJECTED').count(),
        }
        
        context = {
            'applications': applications,
            'status_counts': status_counts,
            'total_applications': applications.count(),
        }
        
        return render(request, 'applications.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading applications: {str(e)}")
        return render(request, 'applications.html', {'applications': [], 'status_counts': {}, 'total_applications': 0})


# US 5.2: Track status of applications
@login_required
@require_POST
@csrf_exempt
def update_application_status(request):
    """US 5.2: As a user I want to be able to track the status of all my applications"""
    try:
        data = json.loads(request.body)
        application_id = data.get('application_id')
        new_status = data.get('status')
        
        if not application_id or not new_status:
            return JsonResponse({'error': 'Missing application_id or status'}, status=400)
        
        # Validate status
        valid_statuses = ['APPLIED', 'INTERVIEW', 'ACCEPTED', 'REJECTED']
        if new_status not in valid_statuses:
            return JsonResponse({'error': 'Invalid status'}, status=400)
        
        # Get the application
        application = get_object_or_404(JobApplication, id=application_id)
        
        # Check if user owns this application
        profile, created = Profile.objects.get_or_create(
            email=request.user.email,
            defaults={
                'firstName': request.user.first_name or '',
                'lastName': request.user.last_name or '',
            }
        )
        
        if application.profileID != profile:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Update status
        application.status = new_status
        application.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Application status updated to {new_status}',
            'new_status': new_status
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# API endpoint to get applications data for AJAX
@login_required
def get_applications_data(request):
    """API endpoint to get applications data for the dashboard"""
    try:
        # Get or create user profile
        profile, created = Profile.objects.get_or_create(
            email=request.user.email,
            defaults={
                'firstName': request.user.first_name or '',
                'lastName': request.user.last_name or '',
            }
        )
        
        # Get all applications for this user
        applications = JobApplication.objects.filter(profileID=profile).order_by('-id')
        
        # Count applications by status
        status_counts = {
            'APPLIED': applications.filter(status='APPLIED').count(),
            'INTERVIEW': applications.filter(status='INTERVIEW').count(),
            'ACCEPTED': applications.filter(status='ACCEPTED').count(),
            'REJECTED': applications.filter(status='REJECTED').count(),
        }
        
        # Prepare applications data for JSON response
        applications_data = []
        for app in applications:
            applications_data.append({
                'id': app.id,
                'company_name': app.jobID.companyName if app.jobID else 'N/A',
                'position': app.jobID.position if app.jobID else 'N/A',
                'status': app.status,
                'status_display': dict(JobApplication.StatusChoices)[app.status],
                'applied_date': app.jobID.created_at.strftime('%Y-%m-%d') if app.jobID and hasattr(app.jobID, 'created_at') else 'N/A',
            })
        
        return JsonResponse({
            'applications': applications_data,
            'status_counts': status_counts,
            'total_applications': applications.count(),
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)