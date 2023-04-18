from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import RegisterSerializer,SendotpSerializer,VerifyOtpSerializer,UserInterestSerializer
from .models import Useraccount,Interest
from .service import *
from .email import *
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated


class RegisterAPI(APIView):
    # def get(self,request):
    #     user = Useraccount.objects.all()
    #     serializer = RegisterSerializer(user, many=True)      
    #     return Response(serializer.data)

    def post(self,request):
        body = request.data
        flag= user_exist(body['email'])
        if flag == True:
            return Response({"status":400,"message":"User already exist"})
        else:
            serializer = RegisterSerializer(data=body)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response({"status":200,"message":"Data saved succesfully"})
            else: 
                return Response({"status":400,"message":"Data Invalid"})

class SendOtpAPI(APIView):
    def post(self, request):
            try:
                data= request.data
                serializer= SendotpSerializer(data = data)
                if serializer.is_valid():
                    serializer.save()
                send_otp(serializer.data['email'])
                return Response({'status': 200,
                                    'message': 'registration successfully Done, check email',
                                    'data': serializer.data})    
        
            except Exception as e:
               return Response({'status': 400,
                             'message': 'Bad request',
                             'data': str(e)})  

class VerifyOtpAPI(APIView):
    def post(self,request):
        try:
            data=request.data
            serializer=VerifyOtpSerializer(data=data)
            
            if serializer.is_valid():
                    email=serializer.data['email']
                    otp=serializer.data['otp']
                    user=Useraccount.objects.filter(email=email)
                    
                    if not user.exists():
                        return Response({'status': 400,
                            'message': 'something went wrong',
                            'data' : 'invalid email'})
                    
                    print(user[0].otp)
                    if not user[0].otp == otp:
                        return Response({'status': 400,
                                    'message': 'something went wrong',
                                    'data': 'Wrong Otp'})
                    
                    user=user.first()
                    user.is_verified=True
                    user.save()
                    return Response({'status': 200,
                                    'message': 'Account Verified',
                                    'data': {}})

            return Response({'status': 400,
                                    'message': 'something went wrong',
                                    'data': serializer.errors})
                                        
        except Exception as e:
            print(e)
             
class LoginAPI(APIView):
    def post(self,request):
        email=request.data.get('email')
        password=request.data.get('password')
        flag=user_validation(email,password)
        if flag==True:
            flag1=user_verification(email)
            if flag1==True:
                user = Useraccount.objects.get(email=email)
                refresh = RefreshToken.for_user(user)
                return Response({"success": True, "message": "Your account has been successfully activated!!",
                                 'refresh': str(refresh),
                                 'access': str(refresh.access_token)},
                                status=status.HTTP_200_OK)
                
            else:
                return Response({"status":400,
                                 "message":"Your email is not verified,First verify it"})
        else:
            return Response({"status":400,"message":"Invalid credentials"})

class UserinterestAPI(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes=[IsAuthenticated]
    def get(self, request):
        interest = Interest.objects.all()
        serializer = UserInterestSerializer(interest, many=True)      
        return Response(serializer.data)

    def post(self, request):
        selected_interests = request.data.get('interests')
        print(selected_interests)
        if not selected_interests:
            return Response({"message": "No interests selected."},
                             status=status.HTTP_400_BAD_REQUEST)
        
        if len(selected_interests) < 2 or len(selected_interests) > 3:
            return Response({"message": "Please select 2-3 interests."},
                             status=status.HTTP_400_BAD_REQUEST)
        user_interests=[]
        for interest_id in selected_interests:
            try:
                interest = Interest.objects.get(id=interest_id)
                print(interest)
                user_interests.append(Useraccount(email=request.user.email,user_interest=interest))
            except Interest.DoesNotExist:
                pass
        Useraccount.objects.bulk_create(user_interests,batch_size=None,ignore_conflicts=False)
        # user=Useraccount.objects.get('interest')
        # user= user_interests
        # user.save() 
        return Response({"message": "Interests saved successfully."}, status=status.HTTP_201_CREATED)



       