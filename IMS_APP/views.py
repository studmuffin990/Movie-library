import csv
from collections import Counter

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from .forms import MovieForm, SignUpForm
from .models import Movie


def _filter_movies(request, movies):
    search = request.GET.get('q', '').strip()[:100]
    genre = request.GET.get('genre', '').strip()
    status = request.GET.get('status', '')
    sort = request.GET.get('sort', 'recent')
    favorites_only = request.GET.get('favorites') == '1'

    if search:
        movies = movies.filter(movie_title__icontains=search)
    if genre:
        movies = movies.filter(genre=genre)
    if status in (Movie.STATUS_WATCHED, Movie.STATUS_UNWATCHED):
        movies = movies.filter(status=status)
    else:
        status = ''
    if favorites_only:
        movies = movies.filter(is_favorite=True)

    ordering = {
        'recent': '-date_added',
        'title': 'movie_title',
        'year': '-release_year',
        'rating': '-rating',
    }
    sort = sort if sort in ordering else 'recent'
    movies = movies.order_by(ordering[sort], 'movie_title')

    return movies, {
        'search': search,
        'genre': genre,
        'status': status,
        'sort': sort,
        'favorites_only': favorites_only,
    }


def _get_library_summary(movies):
    total_movies = movies.count()
    watched_count = movies.filter(status=Movie.STATUS_WATCHED).count()
    unwatched_count = movies.filter(status=Movie.STATUS_UNWATCHED).count()
    rated_movies = movies.exclude(rating=0.0)
    average_rating = 0.0
    if rated_movies.exists():
        average_rating = round(sum(movie.rating for movie in rated_movies) / rated_movies.count(), 1)

    return {
        'total_movies': total_movies,
        'watched_count': watched_count,
        'unwatched_count': unwatched_count,
        'average_rating': average_rating,
        'total_runtime': sum(movie.runtime_minutes or 0 for movie in movies),
    }


def _get_genre_breakdown(movies):
    genre_counts = Counter(
        genre.strip()
        for movie in movies
        for genre in movie.genre.split(',')
        if genre.strip()
    )
    total_genres = sum(genre_counts.values())
    return [
        {
            'name': genre,
            'count': count,
            'percentage': round(count * 100 / total_genres),
        }
        for genre, count in genre_counts.most_common(5)
    ]


def sign_up(request):
    if request.user.is_authenticated:
        return redirect('index')

    form = SignUpForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            user = form.save()
            Movie.objects.filter(owner__isnull=True).update(owner=user)
        login(request, user)
        return redirect('index')

    return render(request, 'registration/signup.html', {'form': form})


@login_required
def index(request):
    all_movies = Movie.objects.filter(owner=request.user)
    movies, filters = _filter_movies(request, all_movies)
    form = MovieForm()

    if request.method == 'POST':
        form = MovieForm(request.POST)
        if form.is_valid():
            movie = form.save(commit=False)
            movie.owner = request.user
            movie.save()
            return redirect('index')

    featured_movie = None
    if all_movies.exists():
        featured_movie = all_movies.order_by('?').first()
        if request.GET.get('surprise') == '1':
            featured_movie = all_movies.order_by('?').first()

    context = {
        'movies': movies,
        'form': form,
        'edit_form': None,
        'editing_movie': None,
        'featured_movie': featured_movie,
        'library_summary': _get_library_summary(all_movies),
        'genre_breakdown': _get_genre_breakdown(all_movies),
        'filters': filters,
        'genres': all_movies.values_list('genre', flat=True).distinct().order_by('genre'),
        'has_movies': all_movies.exists(),
    }
    return render(request, 'movie/home.html', context)

@login_required
def edit_movie(request, movie_id):
    movie = get_object_or_404(Movie, movie_id=movie_id, owner=request.user)
    all_movies = Movie.objects.filter(owner=request.user)
    movies, filters = _filter_movies(request, all_movies)

    if request.method == 'POST':
        form = MovieForm(request.POST, instance=movie)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = MovieForm(instance=movie)

    context = {
        'movies': movies,
        'form': MovieForm(),
        'edit_form': form,
        'editing_movie': movie,
        'featured_movie': all_movies.order_by('?').first(),
        'library_summary': _get_library_summary(all_movies),
        'genre_breakdown': _get_genre_breakdown(all_movies),
        'filters': filters,
        'genres': all_movies.values_list('genre', flat=True).distinct().order_by('genre'),
        'has_movies': all_movies.exists(),
    }
    return render(request, 'movie/home.html', context)


@require_POST
@login_required
def toggle_movie_status(request, movie_id):
    movie = get_object_or_404(Movie, movie_id=movie_id, owner=request.user)
    if movie.status == Movie.STATUS_WATCHED:
        movie.status = Movie.STATUS_UNWATCHED
    else:
        movie.status = Movie.STATUS_WATCHED
        if movie.watched_on is None:
            movie.watched_on = timezone.localdate()
    movie.save(update_fields=['status', 'watched_on'])
    return redirect('index')


@require_POST
@login_required
def toggle_movie_favorite(request, movie_id):
    movie = get_object_or_404(Movie, movie_id=movie_id, owner=request.user)
    movie.is_favorite = not movie.is_favorite
    movie.save(update_fields=['is_favorite'])
    return redirect('index')


@require_POST
@login_required
def delete_movie(request, movie_id):
    movie = get_object_or_404(Movie, movie_id=movie_id, owner=request.user)
    movie.delete()
    return redirect('index')


@login_required
def export_movies(request):
    movies = Movie.objects.filter(owner=request.user).order_by('movie_title')
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="my-movie-library.csv"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow([
        'Title',
        'Genre',
        'Director',
        'Release year',
        'Release date',
        'Watched on',
        'Runtime (minutes)',
        'Rating',
        'Status',
        'Favorite',
        'Description',
    ])
    for movie in movies:
        values = [
            movie.movie_title,
            movie.genre,
            movie.director,
            movie.release_year,
            movie.release_date or '',
            movie.watched_on or '',
            movie.runtime_minutes or '',
            movie.rating,
            movie.status,
            'Yes' if movie.is_favorite else 'No',
            movie.description,
        ]
        values = [
            "'{}".format(value) if str(value).startswith(('=', '+', '-', '@')) else value
            for value in values
        ]
        writer.writerow(values)
    return response
