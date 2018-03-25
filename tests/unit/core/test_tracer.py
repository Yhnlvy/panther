import testtools
import os
from panther.core.tracer.route_finder import RouteFinder
from panther.core.tracer.file_extractor import FileExtractor
from panther.core.tracer.diver import Diver


class TracerTests(testtools.TestCase):

    def setUp(self):
        super(TracerTests, self).setUp()
        self.test_rel_directory = 'examples/tracer'

    def test(self):
        name = 'basic.js'
        file_path = os.path.join(self.test_rel_directory, name)
        rf = RouteFinder()
        routes = rf.create_routes(file_path)
        diver = Diver(routes)
        diver.dive_all(file_path, depth = 3)
