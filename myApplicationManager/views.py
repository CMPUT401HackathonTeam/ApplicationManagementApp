from django.shortcuts import render
import mimetypes
from django.db.models import Q
from django.core.paginator import Paginator
from requests.auth import HTTPBasicAuth
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework import viewsets, permissions, status
from .models import JobApplication, Profile, JobsToApply, Resume
from .serializers import JobApplicationSerializer, ProfileSerializer, JobsToApplySerializer
from django.views.decorators.http import require_http_methods
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User 
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseServerError, JsonResponse
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login, authenticate,get_user_model
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt
import json
from .forms import ProfileForm
from .models import Profile, JobApplication, Resume, JobsToApply,Education, Skills
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages

class MyLoginView(LoginView):
    def form_valid(self, form):
        login(self.request, form.get_user())
        user = form.get_user()
        if not user:
            return redirect("myApplicationManager:register")
        return redirect("myApplicationManager:homepage", userId=user.id) 
    
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


class MyLogoutView(LogoutView):
    next_page = reverse_lazy('myApplicationManager:login')

    def dispatch(self, request):
        messages.success(request, "You have been successfully logged out.")
        return super().dispatch(request)


def homepage(request, userId):
    return render(request, "homePage.html")
    

def register(request):
    from django.contrib.auth.forms import UserCreationForm    
    
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            try:
                newUser = form.save()     
            except Exception as e:
                print(e)
            try:
                newProfile = Profile(user=newUser)    
                print(newProfile.firstName)
                newProfile.save()
                login(request, newUser) 
            except Exception as e:
                print(e)    
            
            return render(request, "createProfile.html")      
    else:
        form = UserCreationForm()
    return render(request, "register.html", {"form": form})

@login_required
def createProfile(request):
    profile = get_object_or_404(Profile, user=request.user)

    if request.method == "POST":
        profile.email = request.POST.get("email", "")
        profile.firstName = request.POST.get("firstName", "")
        profile.lastName = request.POST.get("lastName", "")
        profile.phoneNumber = request.POST.get("phoneNumber", "")
        profile.address = request.POST.get("address", "")
        profile.city = request.POST.get("city", "")
        profile.province = request.POST.get("province", "")
        profile.postalCode = request.POST.get("postalCode", "")
        
        profile.save()
        return redirect("myApplicationManager:homepage", userId=profile.user.id)
    
    return redirect("myApplicationManager:homepage") 
  
@api_view(['GET','PUT'])
def profile_detail_api(request):
    '''
    API endpoint to retrieve profile details
    only intended for front end to fetch a current user's profile from a request
    '''
    profile = get_object_or_404(Profile, user=request.user)
    serializer = ProfileSerializer(profile)
    print(serializer.data)
    return Response({"profile":serializer.data}, status=200)
        
    

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
        print("HERERERER")
        # Get or create user profile
        profile= get_object_or_404(Profile,
            user=request.user
        )
       
        
        # Get all applications for this user
        applications = JobApplication.objects.filter(profileID=profile).order_by('-id')
        print(" THERE ARE THE CURRENT APPLICATIONS", applications[0].profileID)
        print(applications[0].profileID)
        print(applications)
        
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
    
@login_required
def profile_detail(request):
    """Show the logged-in user's profile"""
    profile, created = Profile.objects.get_or_create(
        user=request.user
    )
    return render(request, "homePage.html", {"profile": profile})



@login_required
def profile_edit(request):
    """Edit the logged-in user's profile"""
    profile, created = Profile.objects.get_or_create(
        user=request.user,
        defaults={
            'firstName': request.user.first_name or '',
            'lastName': request.user.last_name or '',
        }
    )

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("myApplicationManager:profile_detail")
    else:
        form = ProfileForm(instance=profile)

    return render(request, "profile_edit.html", {"form": form, "user":request.user,"profile":profile})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def profile_edit_api(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    data = request.data

    profile.firstName = data.get('firstName', profile.firstName)
    profile.lastName = data.get('lastName', profile.lastName)
    profile.email = data.get('email', profile.email)
    profile.phoneNumber = data.get('phoneNumber', profile.phoneNumber)
    profile.street = data.get('street', profile.street)
    profile.city = data.get('city', profile.city)
    profile.province = data.get('province', profile.province)
    profile.postalCode = data.get('postalCode', profile.postalCode)

    try:
        profile.save()
        return Response({"success": True, "message": "Profile updated successfully!"})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=400)


@api_view(['GET'])
@login_required
def get_jobs_to_apply(request):
    user = request.user
    profile = user.profile.first()  # adjust if user can have multiple profiles

    # Jobs the user has NOT applied to yet
    applied_job_ids = JobApplication.objects.filter(profileID=profile).values_list('jobID', flat=True)
    available_jobs = JobsToApply.objects.exclude(jobID__in=applied_job_ids)

    jobs_list = [{
        'jobID': str(job.jobID),
        'companyName': job.companyName,
        'position': job.position,
        'salary': job.salary,
        'jobDetails': job.jobDetails
    } for job in available_jobs]

    return JsonResponse({'jobs': jobs_list})

@login_required
@csrf_exempt
def apply_to_job(request, jobID):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    user = request.user
    profile = user.profile.first()  # adjust if multiple profiles

    try:
        job = JobsToApply.objects.get(jobID=jobID)
    except JobsToApply.DoesNotExist:
        return JsonResponse({'error': 'Job not found'}, status=404)

    # Check if already applied
    if JobApplication.objects.filter(profileID=profile, jobID=job).exists():
        return JsonResponse({'error': 'Already applied'}, status=400)

    JobApplication.objects.create(
        profileID=profile,
        jobID=job,
        status='APPLIED'
    )

    return JsonResponse({'success': True})