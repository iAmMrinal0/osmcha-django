from django.contrib.gis.geos import GEOSGeometry, Polygon

from rest_framework.generics import (
    ListCreateAPIView, ListAPIView, RetrieveUpdateDestroyAPIView,
    RetrieveDestroyAPIView
    )
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import (
    IsAuthenticated, IsAdminUser, BasePermission, SAFE_METHODS
    )

from ..changeset.serializers import (
    ChangesetSerializer, ChangesetSerializerToStaff, ChangesetStatsSerializer
    )
from ..feature.serializers import FeatureSerializer, FeatureSerializerToStaff
from ..changeset.views import StandardResultsSetPagination
from .models import AreaOfInterest, BlacklistedUser
from .serializers import AreaOfInterestSerializer, BlacklistSerializer


def get_geometry_from_filters(data):
    if 'filters' in data.keys():
        if 'geometry' in data['filters'].keys():
            geometry = data['filters'].get('geometry')
            return GEOSGeometry('{}'.format(geometry))
        elif 'in_bbox' in data['filters'].keys():
            geometry = data['filters'].get('in_bbox').split(',')
            return Polygon.from_bbox(geometry)
        else:
            return None
    else:
        return None


class IsOwnerOrReadOnly(BasePermission):
    """Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True
        else:
            return obj.user == request.user


class AOIListCreateAPIView(ListCreateAPIView):
    """
    get:
    List the Areas of Interest of the current logged user.

    post:
    Create an Area of Interest. It requires authentication.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = AreaOfInterestSerializer
    filter_backends = (OrderingFilter,)
    ordering_fields = ('date', 'name')
    ordering = '-date'

    def get_queryset(self):
        if self.request:
            return AreaOfInterest.objects.filter(user=self.request.user)
        else:
            AreaOfInterest.objects.none()

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            geometry=get_geometry_from_filters(self.request.data)
            )


class AOIRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    """
    get:
    Get details about an Area of Interest.
    put:
    Update an Area of Interest. Only the user that created an Area of Interest
    has permissions to update it.
    patch:
    Update an Area of Interest. Only the user that created an Area of Interest
    has permissions to update it.
    delete:
    Delete an Area of Interest. Only the user that created an Area of Interest
    has permissions to delete it.
    """
    queryset = AreaOfInterest.objects.all()
    serializer_class = AreaOfInterestSerializer
    permission_classes = (IsOwnerOrReadOnly,)

    def perform_update(self, serializer):
        serializer.save(
            geometry=get_geometry_from_filters(self.request.data)
            )


class AOIListChangesetsAPIView(ListAPIView):
    """List the changesets that matches the filters and intersects with the
    geometry of an Area Of Interest. It supports pagination and return the data
    in the same way as the changeset list endpoint.
    """
    queryset = AreaOfInterest.objects.all()
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return ChangesetSerializerToStaff
        else:
            return ChangesetSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_object().changesets().select_related(
            'check_user'
            ).prefetch_related('tags', 'reasons')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AOIListFeaturesAPIView(ListAPIView):
    """List the features that matches the filters and intersects with the
    geometry of an Area Of Interest. It supports pagination and return the data
    in the same way as the feature list endpoint.
    """
    queryset = AreaOfInterest.objects.all()
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return FeatureSerializerToStaff
        else:
            return FeatureSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_object().features().select_related(
            'check_user'
            ).prefetch_related('tags', 'reasons')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AOIStatsAPIView(ListAPIView):
    """Return the statistics of the changesets that match an Area of Interest.
    Return the data in the same format as the Changeset Stats view.
    """
    queryset = AreaOfInterest.objects.all()
    serializer_class = ChangesetStatsSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_object().changesets().select_related(
            'check_user'
            ).prefetch_related('tags', 'reasons')

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class BlacklistedUserListCreateAPIView(ListCreateAPIView):
    """
    get:
    List BlacklistedUsers. Only staff users can access this endpoint.
    post:
    Add a user to the Blacklist. Only staff users can add users to the blacklist.
    """
    queryset = BlacklistedUser.objects.all()
    serializer_class = BlacklistSerializer
    permission_classes = (IsAdminUser,)

    def perform_create(self, serializer):
        serializer.save(added_by=self.request.user)


class BlacklistedUserDetailAPIView(RetrieveDestroyAPIView):
    """
    get:
    Get details about a BlacklistedUser.
    delete:
    Delete a User from the Blacklist.
    """
    queryset = BlacklistedUser.objects.all()
    serializer_class = BlacklistSerializer
    permission_classes = (IsAdminUser,)
