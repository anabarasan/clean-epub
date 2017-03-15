"""cleanepub.py"""

# Standard Library
from __future__ import print_function
import argparse
import logging
import os
import shutil
import sys
import zipfile

# Third Party
from lxml import etree
from bs4 import BeautifulSoup


# Where terminal logging should go
LOG_STREAM = sys.stderr

# In this instance we don't want getLogger(__name__), since '__main__'
# is not a very useful name in the log.
SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]
logger = logging.getLogger(SCRIPT_NAME)

class CleanEPub(object):
    """ CleanEPub """
    NAMESPACES = {
        'n':'urn:oasis:names:tc:opendocument:xmlns:container',
        'pkg':'http://www.idpf.org/2007/opf',
        'dc':'http://purl.org/dc/elements/1.1/'
    }

    def __init__(self, epub_file):
        """Load the epub file and fetch the content pages list
        @param epub_file the file path to the epub file to be cleaned
        """

        # remove the .epub extension from the epub file and use it as working directory
        self.workdir = os.path.abspath(epub_file)[:-5]

        self.extract(epub_file)

        # read the container.xml to get the contents file path
        self.container = etree.parse(os.path.join(self.workdir, 'META-INF', 'container.xml'))
        contents_file = self.container.xpath('n:rootfiles/n:rootfile/@full-path',
                                             namespaces=self.NAMESPACES)[0]
        content_file_folder = os.path.dirname(os.path.join(self.workdir, contents_file))

        # read the contenst file to get the pages reference
        self.contents = etree.parse(os.path.join(self.workdir, contents_file))
        pages = self.contents.xpath('/pkg:package/pkg:spine/pkg:itemref',
                                    namespaces=self.NAMESPACES)

        # with pages reference get the list of pages
        for page in pages:
            pageid = page.get('idref')
            pagefilename = self.contents.xpath(
                "/pkg:package/pkg:manifest/pkg:item[@id='%s']/@href" % pageid,
                namespaces=self.NAMESPACES)[0]
            self.clean(os.path.join(content_file_folder, pagefilename))

        self.create_epub()
        self.cleanup()


    def extract(self, epub_file):
        """extract epub file contents to a workdir folder
        @param epub_file the file path to extract"""
        with zipfile.ZipFile(epub_file, 'r') as source_file:
            source_file.extractall(self.workdir)

    def clean(self, content_file):
        """Remove unwanted tags from the content pages
        @param content_file the file which needs to cleaned"""
        with open(content_file, 'r') as source_file:
            original_content = source_file.read()
        soup = BeautifulSoup(original_content, "lxml")
        for match in soup.findAll('span'):
            match.unwrap()
        modified_content = soup.prettify("utf-8")
        with open(content_file, 'w') as destination_file:
            destination_file.write(modified_content)

    def create_epub(self):
        """Create a new epub file with the contents of workdir"""
        with zipfile.ZipFile(self.workdir + '-clean.epub', 'w', zipfile.ZIP_DEFLATED) as clean_epub:
            for root, dirs, files in os.walk(self.workdir):
                for file_ in files:
                    clean_epub.write(os.path.join(root, file_),
                                     os.path.relpath(os.path.join(root, file_),
                                                     os.path.join(self.workdir, '.')))

    def cleanup(self):
        """remove all the files in workdir including the workdir"""
        shutil.rmtree(self.workdir)


def parse_arguments(argv):
    """ Standard argument parsing.

    @param argv - sys.argv.
    @return - tuple of parsed arguments to be unpacked
    """
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawTextHelpFormatter)
    # Required Arguments
    required_args = parser.add_argument_group('required arguments')
    parser.add_argument("--source", "-s",
                        help="path to the input epub file which needs to be processed.",
                        required=True)
    parser.add_argument("--destination", "-d",
                        help="path where to write the processed epub.",
                        required=True)
    # Optional Arguments
    parser.add_argument("--batch", "-b",
                        help="""batch mode.
                        if specified, SOURCE and DESTINATION should be folder paths.""",
                        action="store_true")
    parser.add_argument("--verbose", "-v",
                        help="Verbose mode.",
                        action="store_true")

    args = parser.parse_args(argv)

    return args.source, args.destination, args.batch, args.verbose

def setup_terminal_verbosity(verbose, log_stream):
    """Make the terminal output appropriately verbose.

    @param verbose is True for verbose output (output INFO and up), otherwise
        we output WARNING and up.
    @param log_stream is the stream (typically sys.stderr) whose log handler
        we want to amend to match the requested verbosity.

    If there isn't a handler for @c log_stream on the root logger, then we
    don't do anything.
    """
    # Find the log handler for our stream (terminal) output
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if handler.stream == log_stream:
            break
    else:
        # This should never really happen - there should always be a handler
        # for the terminal - but we might as well be safe.
        handler = None

    if handler:
        # The default level, set up by vxlogging, for the stream output
        # is DEBUG, which is not normally what we want
        if verbose:
            handler.setLevel(logging.INFO)
        else:
            handler.setLevel(logging.WARNING)

def main(args):
    """Do what the program does.
        * parse the command line arguments
        * process the epub files
        * write cleaned epub files

    @param args are the command line arguments, as a list.
    """
    source, destination, batch, verbosity = parse_arguments(args)

    setup_terminal_verbosity(verbosity, LOG_STREAM)

    logger.info('Done.')


if __name__ == '__main__':
    SOURCE_PATH = sys.argv[1]
    # does the given path exist
    if os.path.exists(SOURCE_PATH):
        # is this given path a file or directory
        if os.path.isdir(SOURCE_PATH):
            # batch process
            FILES_IN_DIRECTORY = os.listdir(SOURCE_PATH)
            for path in FILES_IN_DIRECTORY:
                FULL_PATH = os.path.abspath(os.path.join(SOURCE_PATH, path))
                if os.path.isfile(FULL_PATH):
                    print('processing %s' % FULL_PATH)
                    CleanEPub(FULL_PATH)
        elif os.path.isfile(SOURCE_PATH):
            # single file
            CleanEPub(SOURCE_PATH)
        else:
            print('%s is not a file / directory' % SOURCE_PATH)
