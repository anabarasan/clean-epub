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

# In this instance we don't want getLogger(__name__), since '__main__'
# is not a very useful name in the log.
SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]
logger = logging.getLogger(SCRIPT_NAME)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.NullHandler())

NAMESPACES = {
    'n':'urn:oasis:names:tc:opendocument:xmlns:container',
    'pkg':'http://www.idpf.org/2007/opf',
    'dc':'http://purl.org/dc/elements/1.1/'
}

def extract_epub(epub_file):
    """extract epub file contents to a workdir folder
        @param epub_file the file path to extract
        @returns the path where the file was extracted"""
    extract_dir = os.path.abspath(epub_file)[:-5]
    with zipfile.ZipFile(epub_file, 'r') as source_file:
        source_file.extractall(extract_dir)
    return extract_dir


def clean(content_file):
    """Remove unwanted tags from the content pages
    @param content_file the file which needs to cleaned"""
    logger.debug('reading  %s', content_file)
    with open(content_file, 'r') as source_file:
        original_content = source_file.read()
    logger.debug('processing %s', content_file)
    soup = BeautifulSoup(original_content, "lxml")
    for match in soup.findAll('span'):
        match.unwrap()
    modified_content = soup.prettify("utf-8")
    logger.debug('writing cleaned file to %s', content_file)
    with open(content_file, 'w') as destination_file:
        destination_file.write(modified_content)


def create_epub(uncompressed_epub, destination):
    """Create a new epub file with the contents of uncompressed_epub
    @param uncompressed_epub - the folder where the epub files are located
    @param destination - the place where the epub file is to be placed"""
    logger.debug('Writing epub file at %s', destination)
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as clean_epub:
        for root, dirs, files in os.walk(uncompressed_epub):
            for file_ in files:
                clean_epub.write(os.path.join(root, file_),
                                 os.path.relpath(os.path.join(root, file_),
                                                 os.path.join(uncompressed_epub, '.')))


def delete_uncompressed_epub(uncompressed_epub):
    """remove all the files in uncompressed_epub including the uncompressed_epub"""
    logger.debug('removing uncompressed directory %s', uncompressed_epub)
    shutil.rmtree(uncompressed_epub)


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
                        help="path to the input epub file which needs to be processed",
                        required=True)
    parser.add_argument("--destination", "-d",
                        help="path where to write the processed epub",
                        required=True)
    # Optional Arguments
    parser.add_argument("--batch", "-b",
                        help="batch mode. if specified, SOURCE & DESTINATION should be folder path",
                        action="store_true")
    parser.add_argument("--verbose", "-v",
                        help="Verbose mode",
                        action="store_true")

    args = parser.parse_args(argv)

    return args.source, args.destination, args.batch, args.verbose

def setup_terminal_verbosity(verbose):
    """Make the terminal output appropriately verbose.

    @param verbose is True for verbose output (output INFO and up), otherwise
        we output WARNING and up.
    """
    streamhandler = logging.StreamHandler(sys.stderr)

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    streamhandler.setFormatter(formatter)

    if verbose:
        streamhandler.setLevel(logging.DEBUG)
    else:
        streamhandler.setLevel(logging.INFO)

    logger.addHandler(streamhandler)


def process(source, destination):
    """ Load the epub file and fetch the content pages list and clean pages
    @param source - the epub file which is to be cleaned
    @param destination - the destination where the cleaned file is to be placed"""
    source = os.path.abspath(source)
    destination = os.path.abspath(destination)

    logger.info('source file: %s', source)
    logger.info('destination file: %s', destination)

    uncompressed_epub = extract_epub(source)
    logger.debug('Extracted the epub to %s', uncompressed_epub)

    # read the container.xml to get the contents file path
    container_xml = os.path.join(uncompressed_epub, 'META-INF', 'container.xml')
    container = etree.parse(container_xml)
    logger.debug('found container xml at %s', container_xml)

    # read the contenst file to get the pages reference
    contents_file = container.xpath('n:rootfiles/n:rootfile/@full-path',
                                    namespaces=NAMESPACES)[0]
    content_file_folder = os.path.dirname(os.path.join(uncompressed_epub, contents_file))
    logger.debug('content files path -> %s', content_file_folder)
    contents = etree.parse(os.path.join(uncompressed_epub, contents_file))
    pages = contents.xpath('/pkg:package/pkg:spine/pkg:itemref',
                           namespaces=NAMESPACES)

    # with pages reference get the list of pages
    for page in pages:
        pageid = page.get('idref')
        pagefilename = contents.xpath("/pkg:package/pkg:manifest/pkg:item[@id='%s']/@href" % pageid,
                                      namespaces=NAMESPACES)[0]
        pagefilename = os.path.abspath(os.path.join(content_file_folder, pagefilename))

        clean(os.path.join(content_file_folder, pagefilename))

    create_epub(uncompressed_epub, destination)

    delete_uncompressed_epub(uncompressed_epub)


def batch_process(source, destination):
    """ Get the epub file in the source folder and clean each epub file
    @param source - the folder path of the epub files
    @param destination - the folder path where the processed epub files are to be saved"""
    directory_list = os.listdir(source)
    logger.debug('\n'.join(directory_list))
    for path in directory_list:
        source_file = os.path.abspath(os.path.join(source, path))
        source_filename = os.path.basename(source_file)
        destination_file = os.path.join(destination, source_filename)
        if os.path.isfile(source_file):
            process(source_file, destination_file)


def main(args):
    """Do what the program does.

        * parse the command line arguments
        * process the epub files
        * write cleaned epub files

    @param args are the command line arguments, as a list.
    """
    source, destination, batch, verbosity = parse_arguments(args)

    setup_terminal_verbosity(verbosity)

    if batch:
        batch_process(source, destination)
    else:
        process(source, destination)

    logger.info('Done.')


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        print()
    except Exception as e:
        logger.error(e)
        logger.exception(e)
        sys.exit(1)
