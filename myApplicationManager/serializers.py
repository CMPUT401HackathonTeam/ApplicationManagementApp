from rest_framework import serializers
from .models import JobApplication, Profile, JobsToApply, Resume, Education, Experience, Skills

#------------------------------------
# Simple serializers for each model
#------------------------------------
class JobApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplication
        fields = ['id', 'status', 'resumeID', 'jobID', 'profileID']
        read_only_fields = ['id', 'profileID']
    
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'userID', 'firsName', 'lastName', 'email', 'phone', 'address', 'city', 'province', 'postalCode']
        read_only_fields = ['id', 'userID']

class JobsToApplySerializer(serializers.ModelSerializer):
    class Meta:
        model = JobsToApply
        fields = ['id', 'title', 'company', 'location', 'description', 'url']
        read_only_fields = ['id']

#----------------------------------------------------
# Nested serializers for Resume with related models
#----------------------------------------------------

class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = ['id', 'school_name', 'degree', 'start_date', 'end_date', 'description']
        read_only_fields = ['id']

class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = ['id', 'job_title', 'company_name', 'start_date', 'end_date', 'description']
        read_only_fields = ['id']

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skills
        fields = ['id', 'skill_name']
        read_only_fields = ['id']

class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ['id', 'profileID', 'file', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']

    # -------- create --------
    def create(self, validated_data):
        edus = validated_data.pop("education", [])
        jobs = validated_data.pop("jobs", [])
        skills = validated_data.pop("skills", [])

        # userID is provided by view via serializer.save(userID=profile)
        resume = Resume.objects.create(**validated_data)

        for e in edus:
            Education.objects.create(resumeID=resume, **e)
        for j in jobs:
            Experience.objects.create(resumeID=resume, **j)
        for s in skills:
            Skills.objects.create(resumeID=resume, **s)

        return resume

    # -------- update (upsert + soft delete omitted) --------
    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.save()

        def sync_children(related_qs, incoming_items, ModelCls, fk_name="resumeID"):
            existing = {obj.id: obj for obj in related_qs.all()}
            seen_ids = set()

            for item in incoming_items:
                item_id = item.get("id")
                if item_id and item_id in existing:
                    obj = existing[item_id]
                    # update fields except 'id'
                    for k, v in item.items():
                        if k != "id":
                            setattr(obj, k, v)
                    obj.save()
                    seen_ids.add(item_id)
                else:
                    create_kwargs = item.copy()
                    create_kwargs[fk_name] = instance
                    ModelCls.objects.create(**create_kwargs)

            # Soft-delete anything not included this round
            for obj_id, obj in existing.items():
                if obj_id not in seen_ids:
                    obj.delete()

        # Use initial_data to distinguish between "not provided" vs "empty list"
        if "education" in self.initial_data:
            sync_children(instance.education, self.initial_data.get("education", []), Education)
        if "jobs" in self.initial_data:
            sync_children(instance.jobs, self.initial_data.get("jobs", []), Experience)
        if "skills" in self.initial_data:
            sync_children(instance.skills, self.initial_data.get("skills", []), Skills)

        return instance

    # -------- representation (hide soft-deleted children) --------
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["education"] = EducationSerializer(
            instance.education.filter(is_deleted=False), many=True
        ).data
        rep["jobs"] = ExperienceSerializer(
            instance.jobs.filter(is_deleted=False), many=True
        ).data
        rep["skills"] = SkillSerializer(
            instance.skills.filter(is_deleted=False), many=True
        ).data
        return rep
