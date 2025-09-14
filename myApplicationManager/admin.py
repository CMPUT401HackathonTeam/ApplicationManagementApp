from django.contrib import admin
from .models import JobApplication, Resume, Profile, Skills, Education, JobsToApply





class ProfileAdmin(admin.ModelAdmin):
    '''Follow Request Author following objects'''
    def get_queryset(self, request):
        return Profile.all_objects.all()
    def user(self,obj):
        return obj.user.username

    list_display = ["user","firstName", "lastName","profileID"]
    search_fields= ['user']
    
admin.site.register(Profile, ProfileAdmin)
admin.site.register(JobApplication)
admin.site.register(Resume)
admin.site.register(JobsToApply)