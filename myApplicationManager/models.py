from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import QuerySet, Manager
from datetime import datetime
import pytz


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
        
        
class JobApplication(models.Model):
    '''A class representing a job application on the website
       Each Job Application is Associated with a specific user
       FIELDS:
        - Company Name
        - Company Website (optional)
        - Position Name
        - Position Details (optional)
        - Status
    
    '''
    companyName = models.TextField(default="")
    postion = models.TextField(default="")
    
