from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('register/', views.register, name='register'),
    path('product/',views.product,name='product'),
    path('search/', views.search_products, name='search_products'),

]
