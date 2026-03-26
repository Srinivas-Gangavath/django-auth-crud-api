from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import random

from .models import Item, OTP
from .forms import ItemForm, SignupForm, LoginForm, OTPForm

# DRF
from rest_framework import generics, permissions
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .serializers import ItemSerializer

# Signup
def signup_view(request):
    form = SignupForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        user.email = form.cleaned_data.get('email')
        user.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('/')
    return render(request, 'app/signup.html', {'form': form})

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')

# List
@login_required
def item_list(request):
    items = Item.objects.all()
    return render(request, 'app/list.html', {'items': items})

# Create
@login_required
def item_create(request):
    form = ItemForm(request.POST or None)
    if form.is_valid():
        item = form.save(commit=False)
        item.user = request.user   #IMPORTANT
        item.save()
        return redirect('/')
    return render(request, 'app/form.html', {'form': form})

# Update
@login_required
def item_update(request, pk):
    item = get_object_or_404(Item, pk=pk, user=request.user)  #restrict
    form = ItemForm(request.POST or None, instance=item)
    if form.is_valid():
        form.save()
        return redirect('/')
    return render(request, 'app/form.html', {'form': form})

# Delete
@login_required
def item_delete(request, pk):
    item = get_object_or_404(Item, pk=pk, user=request.user)  #restrict
    if request.method == 'POST':
        item.delete()
        return redirect('/')
    return render(request, 'app/confirm_delete.html', {'item': item})

@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)

    if user is not None:
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})
    else:
        return Response({'error': 'Invalid credentials'}, status=400)

def login_view(request):
    form = LoginForm(request.POST or None)

    if form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "No account found with this email")
            return redirect('login')

        user = authenticate(username=user.username, password=password)

        if user:
            if not user.email:
                messages.error(request, "No email found for this user")
                return redirect('login')

            otp_code = OTP.generate_otp()

            # delete old OTPs
            OTP.objects.filter(user=user).delete()

            OTP.objects.create(user=user, code=otp_code)

            send_mail(
                'Your OTP Code',
                f'Your OTP is {otp_code}',
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )

            request.session['user_id'] = user.id

            # ✅ production message
            messages.success(request, "We’ve sent an OTP to your registered email.")

            return redirect('verify_otp')

        else:
            messages.error(request, "Invalid email or password")

    return render(request, 'app/login.html', {'form': form})


# STEP 2: VERIFY OTP
def verify_otp(request):
    form = OTPForm(request.POST or None)

    if form.is_valid():
        otp_entered = form.cleaned_data['otp']
        user_id = request.session.get('user_id')

        if not user_id:
            return redirect('login')

        otp_obj = OTP.objects.filter(user_id=user_id).last()

        if otp_obj:
            # ✅ EXPIRY CHECK (5 mins)
            if timezone.now() - otp_obj.created_at > timedelta(minutes=5):
                messages.error(request, "OTP expired. Please request a new one.")
                return redirect('resend_otp')

            if otp_obj.code == otp_entered:
                user = User.objects.get(id=user_id)
                # login(request, user)
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')

                # साफ session after login
                request.session.pop('user_id', None)

                return redirect('/')
            else:
                messages.error(request, "Invalid OTP")

    return render(request, 'app/verify_otp.html', {'form': form})


def resend_otp(request):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect('login')

    from django.contrib.auth.models import User
    user = User.objects.get(id=user_id)

    #Generate new OTP
    otp_code = str(random.randint(100000, 999999))

    OTP.objects.create(user=user, code=otp_code)

    #Send email again
    send_mail(
        'Your New OTP Code',
        f'Your new OTP is {otp_code}',
        settings.EMAIL_HOST_USER,
        [user.email],
        fail_silently=False,
    )

    from django.contrib import messages
    messages.success(request, "New OTP sent to your email!")

    return redirect('verify_otp')


# LIST + CREATE
class ItemListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ItemSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Item.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# RETRIEVE + UPDATE + DELETE
class ItemDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ItemSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Item.objects.filter(user=self.request.user)
