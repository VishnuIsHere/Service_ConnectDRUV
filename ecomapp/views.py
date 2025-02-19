from rest_framework.views import APIView
from .serializers import RegisterSerializer,OTPVerificationSerializer,ProfileSerializer, ServicesSerializer, SubservicesSerializer, ServiceRegistrySerializer, ServiceRequestSerializer, BookingListSerializer,ReviewSerializer,CreateOrderSerializer, VerifyPaymentSerializer, PaymentSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .manager import create_otp_for_user
from .email import send_otp_via_email
from django.contrib.auth.hashers import check_password
from .models import Register,Profile,Services, Subservices, ServiceRegistry, ServiceRequest,BookingList,Review,Payment,EmployeeRegistration
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView
from rest_framework.decorators import api_view
from .pagination import CustomPagination
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django.conf import settings
from rest_framework.response import Response
import razorpay   
import uuid    



client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


class CreateOrderAPIView(APIView):
    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        if serializer.is_valid():
            amount = serializer.validated_data["amount"]
            user = serializer.validated_data.get("user")
            employee = serializer.validated_data.get("employee")
            currency = "INR"

            data = {
                "amount": int(float(amount) * 100),  # Convert to paise
                "currency": currency,
                "payment_capture": 1
            }

            order = client.order.create(data)
            payment = Payment.objects.create(
                order_id=order["id"], 
                user=user,
                employee=employee,
                amount=amount, 
                status="created",
                reference_number=str(uuid.uuid4())[:10]  # Shorter reference number
            )

            return Response({"order": order, "payment": PaymentSerializer(payment).data}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class VerifyPaymentAPIView(APIView):
    def post(self, request):
        serializer = VerifyPaymentSerializer(data=request.data)
        if serializer.is_valid():
            order_id = serializer.validated_data["order_id"]
            payment_id = serializer.validated_data["payment_id"]
            signature = serializer.validated_data["signature"]

            params_dict = {
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature
            }

            try:
                client.utility.verify_payment_signature(params_dict)
                
                # Update Payment record
                payment = Payment.objects.filter(order_id=order_id).first()
                if payment:
                    payment.payment_id = payment_id
                    payment.status = "paid"
                    payment.save()

                return Response({"message": "Payment successful"}, status=status.HTTP_200_OK)
            except razorpay.errors.SignatureVerificationError:
                Payment.objects.filter(order_id=order_id).update(status="failed")
                return Response({"message": "Payment verification failed"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



    
def welcome(request):
    content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome</title>
        <style>
            body {
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                font-family: Arial, sans-serif;
                background: url('') no-repeat center center fixed;
                background-color: black;
                background-size: cover;
                color: magenta;
                text-shadow: 2px 2px 5px rgba(128, 128, 128, 1);
            }
            h1 {
                font-size: 3rem;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <h1>Welcome to the Service Connect Management System!</h1>
    </body>
    </html>
    """
    return HttpResponse(content)
    
    
    
    
    
    
    
    
    
class RegisterAPIView(APIView):
    permission_classes=[AllowAny]
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully", "user": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 

class LoginAPIView(APIView):
    permission_classes=[IsAuthenticated] 
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({"error": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Register.objects.get(email=email)
            if check_password(password, user.password):
                otp_code = create_otp_for_user(user)

                send_otp_via_email(email, otp_code)   
        
                return Response({"message": "Login successful check your mail", "user": {"id": user.id, "name": user.name, "email": user.email}}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)
        except Register.DoesNotExist:
            return Response({"error": "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)  

class OTPVerificationAPIView(APIView):
    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # Delete OTP after successful verification
            return Response({"message": "OTP verified successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ProfileCreateView(APIView):
    permission_classes = [IsAuthenticated]  

    def get(self, request):
        user = request.user
        try:
            profile = Profile.objects.get(user=user)
            serializer = ProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Profile.DoesNotExist:
            return Response({"message": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        user = request.user
        
        if Profile.objects.filter(user=user).exists():
            return Response({"message": "Profile already exists."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)
            return Response({"message": "Profile created successfully.", "profile": serializer.data}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        user = request.user
        try:
            profile = Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            return Response({"message": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProfileSerializer(profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile updated successfully.", "profile": serializer.data}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        user = request.user
        try:
            profile = Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            return Response({"message": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile partially updated successfully.", "profile": serializer.data}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        user = request.user
        try:
            profile = Profile.objects.get(user=user)
            profile.delete()
            return Response({"message": "Profile deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Profile.DoesNotExist:
            return Response({"message": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)
    

    

class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)             
        
        
        
        
class ServicesAPIView(APIView):
    
    @method_decorator(cache_page(60 * 60))
    @method_decorator(vary_on_headers('Authorization'))
    def get(self, request):
    
        services = Services.objects.all()
        data = []

        for service in services:
            subservices = service.subservices.all() 
            subservices_serializer = SubservicesSerializer(subservices, many=True)
            service_data = {
                "id": service.id,
                "title": service.title,
                "image": service.image.url if service.image else None,
                "description": service.description,
                "status": service.status,
                "subservices": subservices_serializer.data,
            }
            data.append(service_data)

        return Response(data, status=status.HTTP_200_OK)
    
    
    
    
    
    
class ServiceRegistryView(APIView):
    
    def get(self, request):
      
        service_registries = ServiceRegistry.objects.all()
        serializer = ServiceRegistrySerializer(service_registries, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
    
    
    
    
    
    
class ServiceRequestAPIView(APIView):
    permission_classes = [IsAuthenticated] 

    def get(self, request, pk=None):
    
        if pk:
            try:
                service_request = ServiceRequest.objects.get(pk=pk)
                serializer = ServiceRequestSerializer(service_request)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except ServiceRequest.DoesNotExist:
                return Response({"error": "ServiceRequest not found."}, status=status.HTTP_404_NOT_FOUND)

        # If no `pk` is provided, return all service requests
        service_requests = ServiceRequest.objects.all()
        serializer = ServiceRequestSerializer(service_requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
   
        
        data = request.data.copy()  
        data['register'] = request.user.id  
        
        # Serialize the data
        serializer = ServiceRequestSerializer(data=data)
        
        if serializer.is_valid():
            serializer.save()  # Save the new service request
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):

        try:
            service_request = ServiceRequest.objects.get(pk=pk)
        except ServiceRequest.DoesNotExist:
            return Response({"error": "ServiceRequest not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ServiceRequestSerializer(service_request, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
    
        try:
            service_request = ServiceRequest.objects.get(pk=pk)
        except ServiceRequest.DoesNotExist:
            return Response({"error": "ServiceRequest not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ServiceRequestSerializer(service_request, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):

        try:
            service_request = ServiceRequest.objects.get(pk=pk)
        except ServiceRequest.DoesNotExist:
            return Response({"error": "ServiceRequest not found."}, status=status.HTTP_404_NOT_FOUND)

        service_request.delete()
        return Response({"message": "ServiceRequest deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
    
    
    
class BookingListView(APIView):
    def get(self, request):
        bookings = BookingList.objects.select_related('register', 'service_request').all()
        paginator = CustomPagination()
        paginated_queryset = paginator.paginate_queryset(bookings, request, view=self)
        serializer = BookingListSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)




class ReviewAPIView(APIView):

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]  # Only authenticated users can post reviews
        return [AllowAny()]  # Everyone can read reviews

    def get(self, request):
        reviews = Review.objects.select_related('service').all()  # Optimize query
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ReviewSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(user=request.user)  # Assign logged-in user
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
