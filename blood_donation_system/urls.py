from django.contrib import admin
from django.urls import path, include
from donation import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('donation.urls')),
    path('inventory/', views.inventory_list, name='inventory-list'),
    path('inventory/<int:pk>/', views.inventory_detail, name='inventory-detail'),
]
