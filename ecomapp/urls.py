from django.urls import path
from .views import RegisterAPIView,LoginAPIView,OTPVerificationAPIView,ProfileCreateView,LogoutAPIView,ServicesAPIView,ServiceRegistryView,ServiceRequestAPIView,BookingListView,ReviewAPIView,CreateOrderAPIView, VerifyPaymentAPIView
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView 

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('verify-otp/', OTPVerificationAPIView.as_view(), name='verify-otp'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', ProfileCreateView.as_view(), name='profile-create'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('services/', ServicesAPIView.as_view(), name='services'),
    path('service-registry/', ServiceRegistryView.as_view(), name='service-registry'),
    path('service-requests/', ServiceRequestAPIView.as_view(), name='service-request-list'), 
    path('service-requests/<int:pk>/', ServiceRequestAPIView.as_view(), name='service-request-detail'), 
    path('bookings/', BookingListView.as_view(), name='booking-list'),
    path('reviews/', ReviewAPIView.as_view(), name='reviews'),
    path('create-order/', CreateOrderAPIView.as_view(), name='create-order'),
    path('verify-payment/', VerifyPaymentAPIView.as_view(), name='verify-payment'),
]
