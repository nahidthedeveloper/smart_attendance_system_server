from rest_framework import serializers
from authentication.models import Student, Teacher, Account, Department, Batch


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['department']  # Assuming 'name' is the correct field for Department


class BatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batch
        fields = ['batch']  # Assuming 'name' is the correct field for Batch


class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        exclude = ['id', 'user']


class TeacherProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        exclude = ['id', 'user']


class ProfileSerializer(serializers.ModelSerializer):
    semester = serializers.SerializerMethodField()
    batch = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = ['id', 'academic_id', 'email', 'role', 'name', 'avatar', 'department', 'semester', 'batch']

    def get_semester(self, obj):
        if obj.role == 'student' and obj.student:
            return obj.student.semester
        return None

    def get_batch(self, obj):
        if obj.role == 'student' and obj.student and obj.student.batch:
            return obj.student.batch.batch
        return None

    def get_department(self, obj):
        if obj.department:
            return obj.department.department
        return None

    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.avatar:
            return request.build_absolute_uri(obj.avatar.url)
        return None
