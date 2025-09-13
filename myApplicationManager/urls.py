from django.contrib import admin
from django.urls import path, include
from .views import MyLoginView, register,homepage

app_name= 'myApplicationManager'
urlpatterns = [
    # Profile related URLs
    path('admin/', admin.site.urls),
    path('', MyLoginView.as_view(template_name='landingPage.html'), name='login'),
    path('register/', register, name='register'),
    path('home/', homepage, name='homepage'),
    
]