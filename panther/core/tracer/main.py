import argparse
import logging

from panther.core.tracer.diver import Diver
from panther.core.tracer.route_finder import RouteFinder


LOG = logging.getLogger()


def main():
    """POC for the backtrace analysis"""
    parser = argparse.ArgumentParser(
        description='Panther Backtracer',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'entry_points', metavar='entry_points', type=str, nargs='*',
        help='entry points of the project where the routes are defined'
    )
    parser.add_argument(
        '-d', '--debug', dest='debug', action='store_true',
        default=False, help='turn on debug mode'
    )
    parser.add_argument(
        '--depth', dest='depth',
        action='store', default=1, type=int,
        help='maximum analysis depth to backtrace vulnerabilities'
    )

    args = parser.parse_args()

    route_finder = RouteFinder()
    routes = []
    for entry_point in args.entry_points:
        routes.extend(route_finder.fetch_routes(entry_point))
    diver = Diver(routes, args.debug)
    diver.dive_all(entry_point, depth=args.depth)


if __name__ == '__main__':
    main()
