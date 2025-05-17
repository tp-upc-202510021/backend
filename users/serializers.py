from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import User

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid credentials")

        if not user.is_active:
            raise serializers.ValidationError("User is inactive")

        tokens = RefreshToken.for_user(user)

        return {
            'access': str(tokens.access_token),
            'refresh': str(tokens),
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'role': user.role,
            }
        }
    
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'name', 'age', 'preference']
    
    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            name=validated_data['name'],
            age=validated_data['age'],
            preference=validated_data['preference'],
        )
        user.set_password(validated_data['password'])  # 🔐 encripta la contraseña
        user.save()
        return user
