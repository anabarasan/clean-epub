"""cleanepub.py"""

# Standard Library
import zipfile
import os
import shutil
import sys

# Third Party
from lxml import etree
from lxml.html import clean
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

        # read the contenst file to get the pages reference
        self.contents = etree.parse(os.path.join(self.workdir, contents_file))
        pages = self.contents.xpath('/pkg:package/pkg:spine/pkg:itemref',
                                    namespaces=self.NAMESPACES)

        # with pages reference get the list of pages
        self.pages = []
        for page in pages:
            pageid = page.get('idref')
            pagefilename = self.contents.xpath(
                "/pkg:package/pkg:manifest/pkg:item[@id='%s']/@href" % pageid,
                namespaces=self.NAMESPACES)[0]
            self.pages.append(pagefilename)

        self.create_epub()
        self.cleanup()


    def extract(self, epub_file):
        """extract epub file contents to a workdir folder
        @param epub_file the file path to extract"""
        with zipfile.ZipFile(epub_file, 'r') as source_file:
            source_file.extractall(self.workdir)

    def clean(self, content_file):
        """Remove unwanted tags from the content pages"""
        with open(content_file, 'r') as source_file:
            original_content = source_file.read()
        soup = BeautifulSoup(original_content)
        result = str(soup)
        strip = clean.Cleaner(meta=True,
                              style=True,
                              page_structure=True,
                              remove_tags=['FONT', 'font', 'span'])
        content = strip.clean_html(result)
        with open(content_file, 'w') as destination_file:
            destination_file.write(content)

    def create_epub(self):
        """Create a new epub file with the contents of workdir"""
        with zipfile.ZipFile(self.workdir + '-clean.epub', 'w', zipfile.ZIP_DEFLATED) as clean_epub:
            for root, dirs, files in os.walk(self.workdir):
                for file in files:
                    clean_epub.write(os.path.join(root, file),
                                     os.path.relpath(os.path.join(root, file),
                                                     os.path.join(self.workdir, '.')))

    def cleanup(self):
        """remove all the files in workdir including the workdir"""
        shutil.rmtree(self.workdir)


if __name__ == '__main__':
    CleanEPub(sys.argv[1])
