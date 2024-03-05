from django.contrib import admin
from django.urls import path, include
from rest_framework import routers

from authentication.viewset import AuthenticationViewSet

router = routers.DefaultRouter()
router.register(r'auth', AuthenticationViewSet, basename='authentication')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include(router.urls)),
]
