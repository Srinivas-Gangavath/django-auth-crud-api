from django.urls import path
from . import views
from .views import ItemListCreateAPIView, ItemDetailAPIView
from .views import login_api

urlpatterns = [
    path('', views.item_list, name='item_list'),

    path('login/', views.login_view, name='login'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),

    path('create/', views.item_create, name='item_create'),
    path('update/<int:pk>/', views.item_update, name='item_update'),
    path('delete/<int:pk>/', views.item_delete, name='item_delete'),

    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),


    path('api/items/', ItemListCreateAPIView.as_view(), name='api-items'),
    path('api/items/<int:pk>/', ItemDetailAPIView.as_view(), name='api-item-detail'),
    path('api/login/', login_api),
]