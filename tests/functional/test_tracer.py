import os
from panther.core.tracer.diver import Diver
from panther.core.tracer.route_finder import RouteFinder
import testtools


class TracerTests(testtools.TestCase):

    def setUp(self):
        super(TracerTests, self).setUp()
        self.test_rel_directory = 'examples/tracer'

    def test_tracer_manager(self):
        name = 'basic.js'
        file_path = os.path.join(self.test_rel_directory, name)
        rf = RouteFinder()
        routes = rf.fetch_routes(file_path)
        diver = Diver(routes)
        vulnerability_count = diver.dive_all(file_path, depth=3)
        self.assertEqual(vulnerability_count, 2)
        vulnerability_count = diver.dive_all(file_path, depth=2)
        self.assertEqual(vulnerability_count, 1)
