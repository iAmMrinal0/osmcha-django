from datetime import date, timedelta

from django.contrib.gis.geos import Polygon
from django.test import TestCase

from ..filters import ChangesetFilter
from ..filters import Changeset
from .modelfactories import (
    ChangesetFactory, SuspectChangesetFactory, UserFactory,
    HarmfulChangesetFactory, GoodChangesetFactory, SuspicionReasonsFactory,
    TagFactory
    )


class TestChangesetFilter(TestCase):
    def setUp(self):
        self.user = UserFactory(username='test_user')
        self.user_2 = UserFactory(username='test_user_2')
        self.changeset = ChangesetFactory(
            id=2343,
            editor='iD 2.0.2',
            comment='My first edit',
            )
        self.suspect_changeset = SuspectChangesetFactory(
            user='suspect_user',
            uid='343',
            source='Bing',
            imagery_used='Bing'
            )
        self.harmful_changeset = HarmfulChangesetFactory(
            check_user=self.user,
            editor='JOSM 1.5',
            powerfull_editor=True,
            imagery_used='Mapbox, Mapillary'
            )
        self.good_changeset = GoodChangesetFactory(
            check_user=self.user_2,
            source='Mapbox'
            )
        self.reason_1 = SuspicionReasonsFactory(name='possible import')
        self.reason_1.changesets.add(self.suspect_changeset)
        self.reason_2 = SuspicionReasonsFactory(name='suspect word')
        self.reason_2.changesets.add(self.suspect_changeset, self.harmful_changeset)
        self.reason_3 = SuspicionReasonsFactory(name='mass deletion')

    def test_boolean_filters(self):
        self.assertEqual(Changeset.objects.count(), 4)
        self.assertEqual(ChangesetFilter({'checked': 'True'}).qs.count(), 2)
        self.assertEqual(ChangesetFilter({'checked': 'true'}).qs.count(), 2)
        self.assertEqual(ChangesetFilter({'checked': True}).qs.count(), 2)
        self.assertEqual(ChangesetFilter({'checked': 'False'}).qs.count(), 2)
        self.assertEqual(ChangesetFilter({'is_suspect': 'True'}).qs.count(), 3)
        self.assertEqual(ChangesetFilter({'harmful': 'True'}).qs.count(), 1)
        self.assertEqual(ChangesetFilter({'harmful': 'False'}).qs.count(), 1)
        self.assertEqual(
            ChangesetFilter({'powerfull_editor': 'True'}).qs.count(), 1
            )

    def test_geo_filters(self):
        geojson_1 = """{'type': 'Polygon', 'coordinates': [
              [[-2.143, 50.56], [-2.143, 51.986], [2.172, 51.986],
              [2.172, 50.56], [-2.143, 50.56]]
            ]}"""
        self.assertEqual(
            ChangesetFilter({'geometry': geojson_1}).qs.count(), 0
            )
        geojson_2 = """{'type': 'Polygon','coordinates': [
            [[-71.06,44.237], [-71.004,44.237], [-71.004,44.243],
            [-71.06,44.243],[-71.06,44.237]]
            ]}"""
        self.assertEqual(
            ChangesetFilter({'geometry': geojson_2}).qs.count(), 4
            )
        geojson_3 = """{'type': 'Polygon','coordinates': [
            [[-71.05399131, 44.23874266], [-71.04206085, 44.23874266],
            [-71.04206085, 44.24169422],[-71.05399131, 44.24169422],
            [-71.05399131, 44.23874266]]
            ]}"""
        self.assertEqual(
            ChangesetFilter({'geometry': geojson_3}).qs.count(), 4
            )

    def test_users_related_filters(self):
        self.assertEqual(
            ChangesetFilter({'users': 'suspect_user'}).qs.count(), 1)
        self.assertEqual(
            ChangesetFilter({'users': 'suspect_user,test'}).qs.count(), 4
            )
        self.assertEqual(
            ChangesetFilter({'checked_by': self.user.name}).qs.count(), 1
            )
        users = '{},{}'.format(self.user.name, self.user_2.name)
        self.assertEqual(ChangesetFilter({'checked_by': users}).qs.count(), 2)

    def test_id_filters(self):
        self.assertEqual(ChangesetFilter({'ids': '2343,2344'}).qs.count(), 1)

    def test_number_field_filters(self):
        self.assertEqual(ChangesetFilter({'create__gte': 2000}).qs.count(), 3)
        self.assertEqual(ChangesetFilter({'create__lte': 1000}).qs.count(), 1)
        self.assertEqual(ChangesetFilter({'delete__gte': 30}).qs.count(), 3)
        self.assertEqual(ChangesetFilter({'delete__lte': 10}).qs.count(), 1)
        self.assertEqual(ChangesetFilter({'modify__gte': 30}).qs.count(), 0)
        self.assertEqual(ChangesetFilter({'modify__lte': 10}).qs.count(), 4)

    def test_date_field_filter(self):
        tomorrow = date.today() + timedelta(days=1)
        yesterday = date.today() - timedelta(days=1)

        self.assertEqual(
            ChangesetFilter({'date__gte': date.today()}).qs.count(), 4
            )
        self.assertEqual(ChangesetFilter({'date__gte': tomorrow}).qs.count(), 0)
        self.assertEqual(ChangesetFilter({'date__lte': tomorrow}).qs.count(), 4)
        self.assertEqual(ChangesetFilter({'date__lte': yesterday}).qs.count(), 0)

    def test_check_date_field_filter(self):
        tomorrow = date.today() + timedelta(days=1)
        yesterday = date.today() - timedelta(days=1)

        self.assertEqual(
            ChangesetFilter({'check_date__lte': yesterday}).qs.count(), 0
            )
        self.assertEqual(
            ChangesetFilter({'check_date__gte': date.today()}).qs.count(), 2
            )
        self.assertEqual(
            ChangesetFilter({'check_date__lte': tomorrow}).qs.count(), 2
            )
        self.assertEqual(
            ChangesetFilter({'check_date__gte': tomorrow}).qs.count(), 0
            )

    def test_char_field_filters(self):
        # editor field
        self.assertEqual(
            ChangesetFilter({'editor': 'id'}).qs.count(), 1
            )
        self.assertEqual(
            ChangesetFilter({'editor': 'Potlatch 2'}).qs.count(), 2
            )
        # comment field
        self.assertEqual(
            ChangesetFilter({'comment': 'My first edit'}).qs.count(), 1
            )
        self.assertEqual(ChangesetFilter({'comment': 'edit'}).qs.count(), 1)
        self.assertEqual(ChangesetFilter({'comment': 'import'}).qs.count(), 0)
        # source field
        self.assertEqual(ChangesetFilter({'source': 'Mapbox'}).qs.count(), 1)
        self.assertEqual(ChangesetFilter({'source': 'Bing'}).qs.count(), 1)
        self.assertEqual(ChangesetFilter({'source': 'Google'}).qs.count(), 0)
        # imagery_used field
        self.assertEqual(ChangesetFilter({'imagery_used': 'Bing'}).qs.count(), 1)
        self.assertEqual(
            ChangesetFilter({'imagery_used': 'Mapbox'}).qs.count(), 3
            )
        self.assertEqual(
            ChangesetFilter({'imagery_used': 'Mapillary'}).qs.count(), 1
            )

    def test_suspicion_reasons_filter(self):
        self.assertEqual(
            ChangesetFilter({'reasons': '{}'.format(self.reason_1.id)}).qs.count(),
            1
            )
        self.assertEqual(
            ChangesetFilter({'reasons': '{}'.format(self.reason_2.id)}).qs.count(),
            2
            )
        self.assertEqual(
            ChangesetFilter(
                {'reasons': '{},{}'.format(self.reason_1.id, self.reason_2.id)}
                ).qs.count(),
            2
            )
        self.assertEqual(
            ChangesetFilter({'reasons': '{}'.format(self.reason_3.id)}).qs.count(),
            0
            )
        self.assertEqual(
            ChangesetFilter({'reasons': '123'}).qs.count(),
            0
            )
        self.assertEqual(
            ChangesetFilter(
                {'all_reasons': '{},{}'.format(self.reason_1.id, self.reason_2.id)}
                ).qs.count(),
            1
            )
        self.assertIn(
            self.suspect_changeset,
            ChangesetFilter(
                {'all_reasons': '{},{}'.format(self.reason_1.id, self.reason_2.id)}
                ).qs,
            )

    def test_tags_filter(self):
        tag_1 = TagFactory(name='Vandalism')
        tag_1.changesets.add(self.changeset, self.harmful_changeset)
        tag_2 = TagFactory(name='Illegal import')
        tag_2.changesets.add(self.suspect_changeset, self.harmful_changeset)
        tag_3 = TagFactory(name='Small error')

        self.assertEqual(
            ChangesetFilter({'tags': '{}'.format(tag_1.id)}).qs.count(), 2
            )
        self.assertEqual(
            ChangesetFilter({'tags': '{}'.format(tag_2.id)}).qs.count(), 2
            )
        self.assertEqual(
            ChangesetFilter({'tags': '{}'.format(tag_3.id)}).qs.count(), 0
            )
        self.assertEqual(
            ChangesetFilter(
                {'tags': '{},{}'.format(tag_1.id, tag_2.id)}
                ).qs.count(),
            3
            )
        self.assertEqual(
            ChangesetFilter(
                {'all_tags': '{},{}'.format(tag_1.id, tag_2.id)}
                ).qs.count(),
            1
            )
        self.assertIn(
            self.harmful_changeset,
            ChangesetFilter({'all_tags': '{},{}'.format(tag_1.id, tag_2.id)}).qs
            )
        self.assertEqual(
            ChangesetFilter(
                {'all_tags': '{},{}'.format(tag_1.id, tag_3.id)}
                ).qs.count(),
            0
            )


class TestChangesetAreaLowerThan(TestCase):
    def setUp(self):
        ChangesetFactory(
            bbox=Polygon([(0, 0), (0, 3), (3, 3), (3, 0), (0, 0)])
            )
        self.geojson_1 = """{
            'type': 'Polygon',
            'coordinates': [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]
            }"""
        self.geojson_2 = """{
            'type': 'Polygon',
            'coordinates': [[[0, 0], [0, 2], [2, 2], [2, 0], [0, 0]]]
            }"""

    def test_area_lower_than_filter(self):
        # Area of the filter is 9 times lower than the area of the changeset
        self.assertEqual(
            ChangesetFilter({'geometry': self.geojson_1, 'area_lt': 10}).qs.count(),
            1
            )
        self.assertEqual(
            ChangesetFilter({'geometry': self.geojson_1, 'area_lt': 8}).qs.count(),
            0
            )
        # Area of the filter is 4/9 of the area of the changeset
        self.assertEqual(
            ChangesetFilter({'geometry': self.geojson_2, 'area_lt': 3}).qs.count(),
            1
            )
        self.assertEqual(
            ChangesetFilter({'geometry': self.geojson_2, 'area_lt': 2}).qs.count(),
            0
            )
        self.assertEqual(
            ChangesetFilter({'area_lt': 10}).qs.count(),
            1
            )
