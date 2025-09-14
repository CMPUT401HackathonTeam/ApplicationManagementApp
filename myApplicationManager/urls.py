from django.urls import path
from django.contrib import admin
from .views import profile_detail,profile_detail_api,createProfile, profile_edit,profile_edit_api, register,MyLogoutView, MyLoginView, homepage, view_applications, get_applications_data, update_application_status
from django.contrib.auth import views as auth_views

app_name = "myApplicationManager"
urlpatterns = [
    #admin, login, logout
    path('admin/', admin.site.urls),
    path('', MyLoginView.as_view(template_name='landingPage.html'), name='login'),
    path('register/', register, name='register'),
    path('<int:userId>/home/', homepage, name='homepage'),
    path('logout/', MyLogoutView.as_view(next_page='login'), name='logout'),

    # Profile routes
    path('profile/', profile_detail, name='profile_detail'),
    path('profile/edit/', profile_edit, name='profile_edit'),
    path('api/profile/',profile_detail_api, name="profile_detail_api"),
     path('profile/edit/api/', profile_edit_api, name='profile_edit_api'),

     # Profile creation/edit/
    path('profile/create/', createProfile, name='createProfile'),
    
    # US 5.1 & 5.2: Applications functionality
    path('applications/', view_applications, name='view_applications'),
    path('api/applications/', get_applications_data, name='get_applications_data'),
    path('api/applications/update-status/', update_application_status, name='update_application_status'),
]
