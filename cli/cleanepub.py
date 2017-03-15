"""cleanepub.py"""

# Standard Library
from __future__ import print_function
import zipfile
import os
import shutil
import sys

# Third Party
from lxml import etree
from bs4 import BeautifulSoup


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


if __name__ == '__main__':
    SOURCE_PATH = sys.argv[1]
    # does the given path exist?
    if os.path.exists(SOURCE_PATH):
        # is this given path a file or directory?
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
