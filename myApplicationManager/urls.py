from django.contrib import admin
from django.urls import path, include
from .views import MyLoginView, register, homepage, view_applications, update_application_status, get_applications_data

app_name= 'myApplicationManager'
urlpatterns = [
    # Profile related URLs
    path('admin/', admin.site.urls),
    path('', MyLoginView.as_view(template_name='landingPage.html'), name='login'),
    path('register/', register, name='register'),
    path('home/', homepage, name='homepage'),
    
    # US 5.1 & 5.2: Applications functionality
    path('applications/', view_applications, name='view_applications'),
    path('api/applications/', get_applications_data, name='get_applications_data'),
    path('api/applications/update-status/', update_application_status, name='update_application_status'),
]