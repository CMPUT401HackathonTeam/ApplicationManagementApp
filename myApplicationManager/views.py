from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, get_user_model, logout
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes

from .models import JobApplication, Profile, JobsToApply
from .forms import JobApplicationForm, ProfileForm
from .serializers import ProfileSerializer  # used in profile_detail_api

import json


# =========================
# Auth views
# =========================
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

    def dispatch(self, request, *args, **kwargs):
        messages.success(request, "You have been successfully logged out.")
        return super().dispatch(request, *args, **kwargs)


def homepage(request, userId):
    return render(request, "homePage.html")


def register(request):
    from django.contrib.auth.forms import UserCreationForm

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            try:
                newUser = form.save()
                newProfile = Profile(user=newUser)
                newProfile.save()
                login(request, newUser)
            except Exception as e:
                print(e)
            # Send to profile creation page first
            return render(request, "createProfile.html")
    else:
        form = UserCreationForm()
    return render(request, "register.html", {"form": form})


# =========================
# Profile views / APIs
# =========================
@login_required
def createProfile(request):
    profile = get_object_or_404(Profile, user=request.user)

    if request.method == "POST":
        profile.email = request.POST.get("email", "")
        profile.firstName = request.POST.get("firstName", "")
        profile.lastName = request.POST.get("lastName", "")
        profile.phoneNumber = request.POST.get("phoneNumber", "")
        # Accept either 'address' (old form) or 'street' (model)
        profile.street = request.POST.get("address", "") or request.POST.get("street", "")
        profile.city = request.POST.get("city", "")
        profile.province = request.POST.get("province", "")
        profile.postalCode = request.POST.get("postalCode", "")
        profile.save()
        return redirect("myApplicationManager:homepage", userId=profile.user.id)

    return redirect("myApplicationManager:homepage")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_detail_api(request):
    """API endpoint to retrieve the current user's profile"""
    profile = get_object_or_404(Profile, user=request.user)
    serializer = ProfileSerializer(profile)
    return Response({"profile": serializer.data}, status=200)


@login_required
def profile_detail(request):
    """Show the logged-in user's profile"""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return render(request, "homePage.html", {"profile": profile})


@login_required
def profile_edit(request):
    """Edit the logged-in user's profile"""
    profile, _ = Profile.objects.get_or_create(
        user=request.user,
        defaults={'firstName': request.user.first_name or '', 'lastName': request.user.last_name or ''}
    )

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("myApplicationManager:profile_detail")
    else:
        form = ProfileForm(instance=profile)

    return render(request, "profile_edit.html", {"form": form, "user": request.user, "profile": profile})


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


# =========================
# Applications views / APIs
# =========================
@login_required
def view_applications(request):
    """US 5.1: View all applications"""
    try:
        profile, _ = Profile.objects.get_or_create(user=request.user)
        applications = JobApplication.objects.filter(profileID=profile).order_by('-apply_date', '-id')

        status_counts = {
            'APPLIED': applications.filter(stage='APPLIED').count(),
            'INTERVIEW': applications.filter(stage='INTERVIEW').count(),
            'ACCEPTED': applications.filter(stage='ACCEPTED').count(),
            'REJECTED': applications.filter(stage='REJECTED').count(),
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


@login_required
def add_application(request):
    """Add a new job application"""
    if request.method == 'POST':
        form = JobApplicationForm(request.POST)
        if form.is_valid():
            profile, _ = Profile.objects.get_or_create(user=request.user)
            application = form.save(commit=False)
            application.profileID = profile
            application.save()
            messages.success(request, 'Application added successfully!')
            return redirect('myApplicationManager:view_applications')
    else:
        form = JobApplicationForm()

    return render(request, 'add_application.html', {'form': form})


@login_required
@require_POST
@csrf_exempt
def update_application_status(request):
    """US 5.2: Track/update status of applications"""
    try:
        data = json.loads(request.body or "{}")
        application_id = data.get('application_id')
        new_status = data.get('status')

        if not application_id or not new_status:
            return JsonResponse({'error': 'Missing application_id or status'}, status=400)

        valid_statuses = ['APPLIED', 'INTERVIEW', 'ACCEPTED', 'REJECTED']
        if new_status not in valid_statuses:
            return JsonResponse({'error': 'Invalid status'}, status=400)

        application = get_object_or_404(JobApplication, id=application_id)
        profile = get_object_or_404(Profile, user=request.user)

        if application.profileID != profile:
            return JsonResponse({'error': 'Permission denied'}, status=403)

        application.stage = new_status
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


@login_required
def get_applications_data(request):
    """API endpoint to get applications data for the dashboard"""
    try:
        profile = get_object_or_404(Profile, user=request.user)
        applications = JobApplication.objects.filter(profileID=profile).order_by('-id')

        status_counts = {
            'APPLIED': applications.filter(stage='APPLIED').count(),
            'INTERVIEW': applications.filter(stage='INTERVIEW').count(),
            'ACCEPTED': applications.filter(stage='ACCEPTED').count(),
            'REJECTED': applications.filter(stage='REJECTED').count(),
        }

        applications_data = []
        for app in applications:
            applications_data.append({
                'id': app.id,
                'company_name': app.company_name,
                'position': app.position,
                'stage': app.stage,
                'stage_display': dict(JobApplication.StatusChoices).get(app.stage, app.stage),
                'apply_date': app.apply_date.strftime('%Y-%m-%d') if app.apply_date else None,
                'response_date': app.response_date.strftime('%Y-%m-%d') if app.response_date else None,
                'job_url': app.job_url,
                'is_referred': app.is_referred,
            })

        return JsonResponse({
            'applications': applications_data,
            'status_counts': status_counts,
            'total_applications': applications.count(),
        })

    except Exception as e:
        import traceback
        print(f"Error in get_applications_data: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
@csrf_exempt
def update_application_field(request):
    """Inline update a specific field of an application"""
    try:
        data = json.loads(request.body or "{}")
        application_id = data.get('application_id')
        field = data.get('field')
        value = data.get('value')

        if not application_id or not field:
            return JsonResponse({'error': 'Missing application_id or field'}, status=400)

        application = get_object_or_404(JobApplication, id=application_id)
        profile = get_object_or_404(Profile, user=request.user)

        if application.profileID != profile:
            return JsonResponse({'error': 'Permission denied'}, status=403)

        if field == 'company_name':
            application.company_name = value or ''
        elif field == 'position':
            application.position = value or ''
        elif field == 'stage':
            if value not in dict(JobApplication.StatusChoices):
                return JsonResponse({'error': 'Invalid status value'}, status=400)
            application.stage = value
        elif field == 'apply_date':
            from datetime import datetime as _dt
            application.apply_date = _dt.strptime(value, '%Y-%m-%d').date() if value else None
        elif field == 'response_date':
            from datetime import datetime as _dt
            application.response_date = _dt.strptime(value, '%Y-%m-%d').date() if value else None
        elif field == 'job_url':
            application.job_url = value or ''
        elif field == 'is_referred':
            application.is_referred = str(value).lower() == 'true'
        else:
            return JsonResponse({'error': 'Invalid field'}, status=400)

        application.save()
        return JsonResponse({'success': True, 'message': f'Application {field} updated successfully'})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# =========================
# Jobs (no FK on JobApplication; we copy fields)
# =========================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_jobs_to_apply(request):
    """List jobs not yet applied to (compare company+position)"""
    profile = get_object_or_404(Profile, user=request.user)
    applied_pairs = set(
        JobApplication.objects.filter(profileID=profile)
        .values_list('company_name', 'position')
    )
    available = [j for j in JobsToApply.objects.all()
                 if (j.companyName, j.position) not in applied_pairs]

    return JsonResponse({'jobs': [{
        'jobID': str(j.jobID),
        'companyName': j.companyName,
        'position': j.position,
        'salary': j.salary,
        'jobDetails': j.jobDetails
    } for j in available]})


@login_required
@csrf_exempt
def apply_to_job(request, jobID):
    """Create a JobApplication from a JobsToApply entry by copying fields"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    profile = get_object_or_404(Profile, user=request.user)
    try:
        job = JobsToApply.objects.get(jobID=jobID)
    except JobsToApply.DoesNotExist:
        return JsonResponse({'error': 'Job not found'}, status=404)

    already = JobApplication.objects.filter(
        profileID=profile, company_name=job.companyName, position=job.position
    ).exists()
    if already:
        return JsonResponse({'error': 'Already applied'}, status=400)

    JobApplication.objects.create(
        profileID=profile,
        company_name=job.companyName,
        position=job.position,
        stage='APPLIED'
    )
    return JsonResponse({'success': True})