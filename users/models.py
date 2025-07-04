from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        extra_fields.setdefault('role', User.Role.USER)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        USER = 'user', 'User'
        ADMIN = 'admin', 'Admin'

    email = models.EmailField(unique=True, max_length=50)
    password = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=50)
    age = models.PositiveIntegerField()
    friend_game_wins = models.PositiveIntegerField(default=0)

    PREFERENCE_CHOICES = [
        ('loans', 'Loans'),
        ('investments', 'Investments'),
    ]
    preference = models.CharField(max_length=20, choices=PREFERENCE_CHOICES)

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.email} ({self.role})"



class UserFriendship(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    requester = models.ForeignKey('User', related_name='friendships_sent', on_delete=models.CASCADE)
    receiver = models.ForeignKey('User', related_name='friendships_received', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('requester', 'receiver')  

    def __str__(self):
        return f"{self.requester.email} → {self.receiver.email} ({self.status})"