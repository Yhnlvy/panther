import testtools
import os
from panther.core.tracer.route_finder import RouteFinder

class TracerTests(testtools.TestCase):

    def setUp(self):
        super(TracerTests, self).setUp()
        self.test_rel_directory = 'examples/tracer'

    def test(self):
        name = 'basic.js'
        file_path = os.path.join(self.test_rel_directory, name)
        rf = RouteFinder()
        rf.dive_all(file_path)