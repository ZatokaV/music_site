from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # головна
    path("catalog/", views.catalog, name="catalog"),  # каталог з фільтрами
    path('order/', views.order_page, name='order_page'),
    path('order/thanks/', views.order_thanks, name='order_thanks'),
    path("track/<slug:slug>/", views.track_detail, name="track_detail"),
    path("track/<slug:slug>/", views.track_detail, name="track_detail"),
    path("how-it-works/", views.how_it_works, name="how_it_works"),
]
