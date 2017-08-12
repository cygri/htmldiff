"""
Entry Point
-----------
Command-line entry point
"""
# Standard
import os
import argparse
import logging
import sys
import pkg_resources
from os.path import abspath

# Project
from htmldiff.lib import diff_files, gen_side_by_side
from htmldiff.logger import logging_init

# Setup the version string
try:
    pkg_version = '%(prog)s {0}'.format(
        pkg_resources.get_distribution('htmldiff').version
    )
except pkg_resources.DistributionNotFound:
    pkg_version = '%(prog)s Development'
except Exception:
    pkg_version = '%(prog)s Unknown'

LOG = logging.getLogger(__name__)


def diff():
    parser = argparse.ArgumentParser(
        description='Tool for diffing html & xhtml files',
    )
    parser.add_argument('INPUT_FILE1')
    parser.add_argument('INPUT_FILE2')
    parser.add_argument(
        '-o',
        '--output_file',
        action='store',
        dest='out_fn',
        default=None,
        help='[OPTIONAL] Write to given output file instead of stdout'
    )
    parser.add_argument(
        '-a',
        '--accurate-mode',
        help='Use accurate mode instead of risky mode',
        dest='accurate_mode',
        default=False,
        action='store_true'
    )
    parser.add_argument(
        '-s',
        '--side-by-side',
        help='generate a side-by-side comparision instead of inline',
        dest='side_by_side',
        default=False,
        action='store_true'
    )
    parser.add_argument(
        '-V',
        '--version',
        dest='version',
        action='version',
        version=pkg_version,
        help='Display the version number.'
    )
    parser.add_argument(
        '-l',
        '--log-level',
        default='INFO',
        choices=('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'),
        help='Logging level for Montana Scripts.'
    )
    parser.add_argument(
        '-L',
        '--logfile',
        dest='logfile',
        default=None,
        help='Location to place a log of the process output'
    )
    parsed_args = parser.parse_args()

    logging_init(parsed_args.log_level, logfile=parsed_args.logfile)
    input_file1 = abspath(parsed_args.INPUT_FILE1)
    input_file2 = abspath(parsed_args.INPUT_FILE2)
    output_file = abspath(parsed_args.out_fn) if parsed_args.out_fn else None
    accurate_mode = parsed_args.accurate_mode
    sbs = parsed_args.side_by_side
    if sbs:
        LOG.info('Selected side-by-side diff')
    else:
        LOG.info('Selected inline diff')

    if not os.path.exists(input_file1):
        LOG.error('Could not find: {0}'.format(input_file1))
        sys.exit(1)

    if not os.path.exists(input_file2):
        LOG.error('Could not find: {0}'.format(input_file2))
        sys.exit(1)

    LOG.debug('File 1: {0}'.format(input_file1))
    LOG.debug('File 2: {0}'.format(input_file2))

    if parsed_args.accurate_mode:
        LOG.debug("Using 'Accurate' mode")
    else:
        LOG.debug("Using 'Risky' mode")

    LOG.info('Diffing files...')
    try:
        diffed_html = diff_files(input_file1, input_file2, accurate_mode)
        if sbs:
            diffed_html = gen_side_by_side(diffed_html)
    except Exception:
        LOG.exception('Diff process exited with an error')
        sys.exit(1)

    if output_file is None:
        sys.stdout.write(diffed_html)
    else:
        try:
            with open(output_file, 'w') as f:
                f.seek(0)
                f.truncate()
                f.write(diffed_html)
        except Exception:
            LOG.exception('Unable to write diff to {0}'.format(output_file))
            sys.exit(1)
        else:
            LOG.info('Wrote diff to {0}'.format(output_file))
            sys.exit(0)


def main():
    import time
    t = time.time()
    try:
        diff()
    except KeyboardInterrupt:
        # Write a nice message to stderr
        sys.stderr.write(
            u"\n\u2717 Operation canceled by user.\n"
        )
        sys.exit(1)

    sys.stderr.write('Took {0:0.4f} seconds\n'.format(time.time() - t))

if __name__ == '__main__':
    main()
