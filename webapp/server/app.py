#!/usr/bin/env python
"""
app.py
server side for cleaning a epub file.
    uploading a epub file
    removing the span tags
    repackage and deliver to user
"""
# Standard Library
import logging
import os
import time

# Bottle
from bottle import Bottle, error, HTTPError, request, response, run


# configuration
APP_DB = 'data.sqlite3'
LOGLEVEL_CONSOLE = logging.INFO
LOGLEVEL_FILE = logging.INFO


# logger
logger = logging.getLogger('app')
logger.setLevel(logging.DEBUG)
FORMATTER = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s')
# Console Logging
CH = logging.StreamHandler()
CH.setLevel(LOGLEVEL_CONSOLE)
CH.setFormatter(FORMATTER)
logger.addHandler(CH)
# File Logging
FH = logging.handlers.RotatingFileHandler('cleanepub.log', maxBytes=1024, backupCount=5)
FH.setLevel(LOGLEVEL_FILE)
FH.setFormatter(FORMATTER)
logger.addHandler(FH)


# File upload max size
MAX_SIZE = 10 * 1024 * 1024 # 10MB
BUF_SIZE = 8192


app = Bottle()


@app.route('/')
def index():
    """returns hello world text for initial route"""
    return """
    <h1>Hello World</h1><br/>
    <form action="/api/v1/clean" method="post" enctype="multipart/form-data">
        Select a file: <input type="file" name="upload" /><br/>
        <input type="submit" value="Start upload" />
    </form>
    """


@app.route('/api/v1/clean', method='POST')
def get_epub():
    """get the user uploaded file and save to disk"""
    epub = request.files.get('upload')
    name, ext = os.path.splitext(epub.filename)

    if ext != '.epub':
        return HTTPError(400, 'File not allowed')

    data_blocks = []
    byte_count = 0

    buf = epub.file.read(BUF_SIZE)
    while buf:
        byte_count += len(buf)

        if byte_count > MAX_SIZE:
            raise HTTPError(413, 'Request entity too large (max: {} bytes)'.format(MAX_SIZE))

        data_blocks.append(buf)
        buf = epub.file.read(BUF_SIZE)

    data = ''.join(data_blocks)
    unique_file_identifier = str(time.time() * 1000)
    file('{0}_{1}'.format(unique_file_identifier, epub.filename), 'wb').write(data)
    response.status = 202
    # @TODO start the conversion process and return queue location


if __name__ == '__main__':
    run(app, host='localhost', port='8000', reloader=True, debug=True)
