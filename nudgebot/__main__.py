import argparse

import github

from config import config
from nudgebot.db import db


argparser = argparse.ArgumentParser()
subparsers = argparser.add_subparsers(help='Operations', dest='operation')
run_parser = subparsers.add_parser('run', help='Running the Bot')
dump_db_parser = subparsers.add_parser('dump_db', help='Dumping all the DB content')
dump_db_parser.add_argument('--filename', '-f', help='The file path to dump the DB content', default=None)
clear_db_parser = subparsers.add_parser('clear_db', help='Clearing all the DB content (DANGER)')
clear_db_parser.add_argument('--force', '-f', dest='force', help='Force operation (without prompt)',
                             action='store_true', default=False)


if config().config.debug_mode:
    github.enable_console_debug_logging()


def parse_command(namespace):
    if namespace.operation == 'run':
        import nudgebot.server as server
        server.run()
    elif namespace.operation == 'dump_db':
        print(db().dump(namespace.filename))
    elif namespace.operation == 'clear_db':
        if namespace.force:
            db().clear_db()
        else:
            ans = raw_input('Are you sure? this operation cannot be undone (n/y): ')
            while ans not in ('y', 'n'):
                ans = raw_input('Please answer "y" or "n": ')
            if ans.lower() in ('n', 'no'):
                return
            elif ans.lower() in ('y', 'yes'):
                return db().clear_db()


if __name__ == '__main__':
    parse_command(argparser.parse_args())
