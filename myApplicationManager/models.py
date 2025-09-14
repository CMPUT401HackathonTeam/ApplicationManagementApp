from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import QuerySet, Manager
from datetime import datetime, date
import pytz
import uuid


def get_mst_time():
    edmonton_timezone = pytz.timezone("America/Edmonton")
    naive_now = datetime.now()
    aware_now = edmonton_timezone.localize(naive_now)
    return aware_now
        
class AppQuerySet(QuerySet):
    '''App Query Set that inherits from Django's defalt app query set
    - enables queries to update to is_deleted instead of hard deletion in the database'''
    def delete(self):
        self.update(is_deleted=True)
  
  
class AppManager(Manager):
    '''A manager that exterds from the default django app manager
        - this manager enables queries to ignore soft-deleted data
        
        '''
    def get_queryset(self):
        return AppQuerySet(self.model, using=self._db).exclude(is_deleted=True)
  
  
class BaseModel(models.Model):
    '''
       A model that extends from the Django base model
     - this model is capable of soft deletion so that deleted entities are still visible in the database  to administors
     - this way, all deleted data is visible in admin dashboards until permenantly deleted by an administrator
    '''
    class Meta:
        abstract = True
  
    is_deleted = models.BooleanField(default=False)
    
    def delete(self):
        self.is_deleted = True
        self.save()
        
        
class JobApplication(BaseModel):
    '''A class representing a job application on the website
       Each Job Application is Associated with a specific user
       FIELDS:
        - Company Name
        - Company Website (optional)
        - Position Name
        - Position Details (optional)
        - Status
        - Apply Date
        - Response Date
        - Job URL
        - Referral Status
    
    '''
    StatusChoices=[
        ('APPLIED', 'Applied'),
        ('INTERVIEW', 'Interview'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    ]
    company_name = models.CharField(max_length=200, default='')
    position = models.CharField(max_length=200, default='')
    stage = models.CharField(max_length=20, choices=StatusChoices, default='APPLIED')
    apply_date = models.DateField(default=date.today, null=True, blank=True)
    response_date = models.DateField(null=True, blank=True)
    job_url = models.CharField(max_length=500, blank=True)
    is_referred = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    resumeID = models.ForeignKey('Resume', on_delete=models.CASCADE, null=True, blank=True)
    profileID = models.ForeignKey('Profile', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

class Profile(BaseModel):
    '''A class representing a user of the application
       FIELDS:
        - Username
        - Password
        - Email
        - First Name
        - Last Name
    '''
    profileID = models.UUIDField(primary_key=True, editable=False, unique=True, default=uuid.uuid4)
    email = models.EmailField(unique=True)
    firstName = models.CharField(max_length=30, default="")
    lastName = models.CharField(max_length=30, default="")
    phoneNumber = models.CharField(max_length=15, default="")
    address = models.TextField(default="")
    city = models.CharField(max_length=50, default="")
    province = models.CharField(max_length=50, default="")
    postalCode = models.CharField(max_length=10, default="")

class JobsToApply(BaseModel):
    '''A class representing a job that a user wants to apply to in the future
       Each JobsToApply is associated with a specific user
       FIELDS:
        - Company Name
        - Position Name
        - Salary (optional)
        - Job Details (optional)
    '''
    jobID = models.UUIDField(primary_key=True, editable=False, unique=True, default=uuid.uuid4)
    companyName = models.TextField(default="")
    position = models.TextField(default="")
    salary = models.TextField(default="")
    jobDetails = models.TextField(default="")

class Resume(BaseModel):
    '''A class representing a resume uploaded by a user
       Each Resume is associated with a specific user
       FIELDS:
        - Resume File (PDF)
        - Upload Date
    '''
    resumeID = models.UUIDField(primary_key=True, editable=False, unique=True, default=uuid.uuid4)
    name = models.TextField(default="")
    userID = models.ForeignKey('Profile', on_delete=models.CASCADE)
    uploadDate = models.DateTimeField(default=get_mst_time)

class Education(BaseModel):
    """Stores a single education entry for a resume"""
    resumeID = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='education')
    school_name = models.CharField(max_length=255)
    degree = models.CharField(max_length=255, blank=True)  # e.g., "B.Sc. in Computer Science"
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)  # blank if ongoing
    description = models.TextField(blank=True)

class Experience(BaseModel):
    """Stores a single work experience entry for a resume"""
    resumeID = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='jobs')
    job_title = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)  # blank if current job
    description = models.TextField(blank=True)

class Skills(BaseModel):
    """Stores a single skill entry for a resume"""
    resumeID = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='skills')
    skill_name = models.CharField(max_length=255)
    proficiency_level = models.CharField(max_length=50,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
            ('expert', 'Expert'),
        ],
        default='beginner')
