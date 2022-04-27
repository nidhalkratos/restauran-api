from django.urls import path 
from . import views

urlpatterns = [
    path('restaurant-create',views.addRestaurant),
    path('menu-create',views.addMenuToRestaurant),
    path('menus',views.getCurrentDayMenus),
    path('vote',views.voteForRestaurantMenu),
    path('result',views.getCurrentDayVotingResults),
    path('login',views.login),
    path('register',views.register),
]