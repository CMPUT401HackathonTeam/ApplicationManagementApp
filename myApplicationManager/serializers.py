from rest_framework import serializers
from .models import JobApplication, Profile, JobsToApply, Resume


class JobApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplication
        fields = ['id', 'status', 'resumeID', 'jobID', 'profileID']
        read_only_fields = ['id', 'profileID']

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["email",
        "firstName",
        "lastName",
        "phoneNumber",
        "street",
        "city",
        "province",
        "postalCode"]
        
        