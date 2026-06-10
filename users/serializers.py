from rest_framework import serializers
from .models import School, SchoolMembership, User


class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ['id', 'code', 'name', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class SchoolMembershipSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    school_code = serializers.CharField(source='school.code', read_only=True)
    school_name = serializers.CharField(source='school.name', read_only=True)

    class Meta:
        model = SchoolMembership
        fields = ['id', 'school', 'school_code', 'school_name', 'user', 'user_email', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at', 'school_code', 'school_name', 'user_email']


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=8)
    default_school_code = serializers.CharField(source='default_school.code', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'password',
            'role',
            'default_school',
            'default_school_code',
            'first_name',
            'last_name',
            'is_staff',
            'is_active',
            'date_joined',
        ]
        read_only_fields = ['id', 'date_joined']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance
