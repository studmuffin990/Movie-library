from django.conf import settings
from django.db import models


class Movie(models.Model):
    movie_id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='movies',
        null=True,
        blank=True,
    )
    movie_title = models.CharField(max_length=255)
    genre = models.CharField(max_length=100)
    director = models.CharField(max_length=255)
    release_year = models.PositiveIntegerField()
    release_date = models.DateField(null=True, blank=True)
    rating = models.FloatField(default=0.0)
    description = models.TextField(blank=True)
    is_favorite = models.BooleanField(default=False)

    STATUS_WATCHED = 'Watched'
    STATUS_UNWATCHED = 'Unwatched'
    STATUS_CHOICES = [
        (STATUS_WATCHED, 'Watched'),
        (STATUS_UNWATCHED, 'Unwatched'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_UNWATCHED,
    )
    date_added = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.movie_title
