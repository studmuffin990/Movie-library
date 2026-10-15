from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import Movie


class AddMovieTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='movie-fan', password='StrongPass!1234')
        self.client.force_login(self.user)

    def test_home_page_has_add_movie_button_and_dialog_form(self):
        response = self.client.get(reverse('index'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add a movie')
        self.assertContains(response, '<dialog')
        self.assertContains(response, 'name="movie_title"')

    def test_valid_movie_submission_creates_movie_and_redirects(self):
        response = self.client.post(
            reverse('index'),
            {
                'movie_title': 'Arrival',
                'genre': 'Sci-Fi',
                'director': 'Denis Villeneuve',
                'release_year': 2016,
                'release_date': '2016-11-11',
                'rating': 8.0,
                'description': 'A linguist works to communicate with visitors.',
                'status': Movie.STATUS_WATCHED,
            },
        )

        self.assertRedirects(response, reverse('index'))
        self.assertTrue(
            Movie.objects.filter(movie_title='Arrival', owner=self.user).exists()
        )


class CollectionFeatureTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='curator', password='StrongPass!1234')
        self.client.force_login(self.user)
        self.arrival = Movie.objects.create(
            owner=self.user,
            movie_title='Arrival',
            genre='Sci-Fi',
            director='Denis Villeneuve',
            release_year=2016,
            rating=8.0,
            status=Movie.STATUS_WATCHED,
        )
        Movie.objects.create(
            owner=self.user,
            movie_title='Dune',
            genre='Sci-Fi',
            director='Denis Villeneuve',
            release_year=2021,
            rating=8.5,
            status=Movie.STATUS_UNWATCHED,
        )
        Movie.objects.create(
            owner=self.user,
            movie_title='The Grand Budapest Hotel',
            genre='Comedy',
            director='Wes Anderson',
            release_year=2014,
            rating=7.9,
        )

    def test_filters_movies_by_title_genre_and_status(self):
        response = self.client.get(
            reverse('index'),
            {'q': 'a', 'genre': 'Sci-Fi', 'status': Movie.STATUS_WATCHED},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['movies']), [self.arrival])

    def test_sorting_by_rating_orders_movies_highest_first(self):
        response = self.client.get(reverse('index'), {'sort': 'rating'})

        self.assertEqual(
            [movie.movie_title for movie in response.context['movies']],
            ['Dune', 'Arrival', 'The Grand Budapest Hotel'],
        )

    def test_favorite_toggle_and_favorites_filter(self):
        response = self.client.post(
            reverse('toggle_movie_favorite', args=[self.arrival.movie_id])
        )

        self.assertRedirects(response, reverse('index'))
        self.arrival.refresh_from_db()
        self.assertTrue(self.arrival.is_favorite)

        response = self.client.get(reverse('index'), {'favorites': '1'})
        self.assertEqual(list(response.context['movies']), [self.arrival])

    def test_user_cannot_toggle_another_users_favorite(self):
        other_user = User.objects.create_user(username='visitor', password='StrongPass!1234')
        self.client.force_login(other_user)

        response = self.client.post(
            reverse('toggle_movie_favorite', args=[self.arrival.movie_id])
        )

        self.assertEqual(response.status_code, 404)
        self.arrival.refresh_from_db()
        self.assertFalse(self.arrival.is_favorite)


class DeleteMovieTests(TestCase):
    def setUp(self):
        self.movie = Movie.objects.create(
            owner=User.objects.create_user(
                username='movie-fan',
                password='StrongPass!1234',
            ),
            movie_title='Inception',
            genre='Sci-Fi',
            director='Christopher Nolan',
            release_year=2010,
        )
        self.client.force_login(self.movie.owner)

    def test_toggle_status_marks_movie_watched_and_back_to_watchlist(self):
        response = self.client.post(
            reverse('toggle_movie_status', args=[self.movie.movie_id])
        )

        self.assertRedirects(response, reverse('index'))
        self.movie.refresh_from_db()
        self.assertEqual(self.movie.status, Movie.STATUS_WATCHED)

        self.client.post(reverse('toggle_movie_status', args=[self.movie.movie_id]))
        self.movie.refresh_from_db()
        self.assertEqual(self.movie.status, Movie.STATUS_UNWATCHED)

    def test_toggle_status_rejects_get_requests(self):
        response = self.client.get(
            reverse('toggle_movie_status', args=[self.movie.movie_id])
        )

        self.assertEqual(response.status_code, 405)
        self.movie.refresh_from_db()
        self.assertEqual(self.movie.status, Movie.STATUS_UNWATCHED)

    def test_user_cannot_toggle_another_users_movie(self):
        other_user = User.objects.create_user(
            username='another-fan',
            password='AnotherPass!1234',
        )
        self.client.force_login(other_user)

        response = self.client.post(
            reverse('toggle_movie_status', args=[self.movie.movie_id])
        )

        self.assertEqual(response.status_code, 404)
        self.movie.refresh_from_db()
        self.assertEqual(self.movie.status, Movie.STATUS_UNWATCHED)

    def test_delete_movie_removes_movie_and_redirects(self):
        response = self.client.post(
            reverse('delete_movie', args=[self.movie.movie_id])
        )

        self.assertRedirects(response, reverse('index'))
        self.assertFalse(Movie.objects.filter(movie_id=self.movie.movie_id).exists())

    def test_delete_movie_rejects_get_requests(self):
        response = self.client.get(
            reverse('delete_movie', args=[self.movie.movie_id])
        )

        self.assertEqual(response.status_code, 405)
        self.assertTrue(Movie.objects.filter(movie_id=self.movie.movie_id).exists())

    def test_user_cannot_delete_another_users_movie(self):
        other_user = User.objects.create_user(
            username='another-fan',
            password='AnotherPass!1234',
        )
        self.client.force_login(other_user)

        response = self.client.post(
            reverse('delete_movie', args=[self.movie.movie_id])
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Movie.objects.filter(movie_id=self.movie.movie_id).exists())


class AccountTests(TestCase):
    def test_login_and_signup_pages_render(self):
        login_response = self.client.get(reverse('login'))
        signup_response = self.client.get(reverse('signup'))

        self.assertEqual(login_response.status_code, 200)
        self.assertContains(login_response, 'Welcome back')
        self.assertEqual(signup_response.status_code, 200)
        self.assertContains(signup_response, 'Create your account')

    def test_library_requires_login(self):
        response = self.client.get(reverse('index'))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('index')}",
        )

    def test_signup_claims_existing_movies_and_logs_user_in(self):
        legacy_movie = Movie.objects.create(
            movie_title='Arrival',
            genre='Sci-Fi',
            director='Denis Villeneuve',
            release_year=2016,
        )

        response = self.client.post(
            reverse('signup'),
            {
                'username': 'first-viewer',
                'password1': 'ComplexPass!2026',
                'password2': 'ComplexPass!2026',
            },
        )

        self.assertRedirects(response, reverse('index'))
        user = User.objects.get(username='first-viewer')
        legacy_movie.refresh_from_db()
        self.assertEqual(legacy_movie.owner, user)
        self.assertTrue(user.check_password('ComplexPass!2026'))
        self.assertIn('_auth_user_id', self.client.session)

    def test_movies_are_private_to_their_owner(self):
        user = User.objects.create_user(username='owner', password='StrongPass!1234')
        other_user = User.objects.create_user(
            username='visitor',
            password='AnotherPass!1234',
        )
        Movie.objects.create(
            owner=user,
            movie_title='Private Film',
            genre='Drama',
            director='A Director',
            release_year=2020,
        )

        self.client.force_login(other_user)
        response = self.client.get(reverse('index'))

        self.assertNotContains(response, 'Private Film')

    def test_user_cannot_edit_another_users_movie(self):
        owner = User.objects.create_user(username='owner', password='StrongPass!1234')
        other_user = User.objects.create_user(
            username='visitor',
            password='AnotherPass!1234',
        )
        movie = Movie.objects.create(
            owner=owner,
            movie_title='Private Film',
            genre='Drama',
            director='A Director',
            release_year=2020,
        )

        self.client.force_login(other_user)
        response = self.client.get(
            reverse('edit_movie', args=[movie.movie_id])
        )

        self.assertEqual(response.status_code, 404)
