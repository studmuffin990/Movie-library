from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('accounts/signup/', views.sign_up, name='signup'),
    path(
        'accounts/login/',
        auth_views.LoginView.as_view(template_name='registration/login.html'),
        name='login',
    ),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', views.index, name='index'),
    path('dashboard/', views.index, name='dashboard'),
    path('movie/<int:movie_id>/edit/', views.edit_movie, name='edit_movie'),
    path('movie/<int:movie_id>/toggle-status/', views.toggle_movie_status, name='toggle_movie_status'),
    path('movie/<int:movie_id>/toggle-favorite/', views.toggle_movie_favorite, name='toggle_movie_favorite'),
    path('movie/<int:movie_id>/delete/', views.delete_movie, name='delete_movie'),
    path('movies/export/', views.export_movies, name='export_movies'),
]