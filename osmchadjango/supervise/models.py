import uuid

from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField

from osmchadjango.changeset.filters import ChangesetFilter
from osmchadjango.feature.filters import FeatureFilter

from ..users.models import User


class AreaOfInterest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True)
    user = models.ForeignKey('users.User')
    date = models.DateTimeField(auto_now_add=True)
    filters = JSONField()
    geometry = models.GeometryField(blank=True, null=True)
    objects = models.GeoManager()

    def __str__(self):
        return '{} by {}'.format(self.name, self.user.username)

    def changesets(self):
        """Return the changesets that match the filters, including the geometry
        area, of the AreaOfInterest.
        """
        qs = ChangesetFilter(self.filters).qs
        if self.geometry is not None:
            return qs.filter(
                bbox__intersects=self.geometry
                )
        else:
            return qs

    def features(self):
        """Return the features that match the filters, including the geometry
        area, of the AreaOfInterest.
        """
        qs = FeatureFilter(self.filters).qs
        if self.geometry is not None:
            return qs.filter(
                geometry__intersects=self.geometry
                )
        else:
            return qs

    class Meta:
        unique_together = ('user', 'name',)
        ordering = ['-date']
        verbose_name = 'Area of Interest'
        verbose_name_plural = 'Areas of Interest'


class BlacklistedUser(models.Model):
    username = models.CharField(max_length=1000, unique=True)
    added_by = models.ForeignKey(User)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        self.full_clean()
        super(BlacklistedUser, self).save(*args, **kwargs)
