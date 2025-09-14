from django.urls import path, include
from django.contrib import admin
from django.contrib.auth import views as auth_views

from .views import (
    # Auth
    MyLoginView,
    MyLogoutView,
    register,

    # Homepage
    homepage,

    # Profile
    profile_detail,
    profile_detail_api,
    createProfile,
    profile_edit,
    profile_edit_api,

    # Applications
    view_applications,
    add_application,
    get_applications_data,
    update_application_status,
    update_application_field,

    # Jobs
    get_jobs_to_apply,
    apply_to_job,
)

app_name = "myApplicationManager"

urlpatterns = [
    # Admin + Auth
    path('admin/', admin.site.urls),
    path('', MyLoginView.as_view(template_name='landingPage.html'), name='login'),
    path('register/', register, name='register'),
    path('<int:userId>/home/', homepage, name='homepage'),
    path('logout/', MyLogoutView.as_view(next_page='login'), name='logout'),

    # Profile routes
    path('profile/', profile_detail, name='profile_detail'),
    path('profile/edit/', profile_edit, name='profile_edit'),
    path('api/profile/', profile_detail_api, name="profile_detail_api"),
    path('profile/edit/api/', profile_edit_api, name='profile_edit_api'),
    path('profile/create/', createProfile, name='createProfile'),

    # Applications functionality
    path('applications/', view_applications, name='view_applications'),
    path('applications/add/', add_application, name='add_application'),
    path('api/applications/', get_applications_data, name='get_applications_data'),
    path('api/applications/update-status/', update_application_status, name='update_application_status'),
    path('api/applications/update-field/', update_application_field, name='update_application_field'),

    # Jobs
    path('api/jobs-to-apply/', get_jobs_to_apply, name='get_jobs_to_apply'),
    path('apply-to-job/<uuid:jobID>/', apply_to_job, name='apply_to_job'),
]