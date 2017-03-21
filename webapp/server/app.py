#!/usr/bin/env python
"""
app.py
server side for cleaning a epub file.
    uploading a epub file
    removing the span tags
    repackage and deliver to user
"""
# Standard Library
import json
import logging
import os
import time

# Bottle
from bottle import Bottle, error, HTTPError, request, response, run

# app import
import db

# configuration
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
    filename = '{0}_{1}'.format(unique_file_identifier, epub.filename)
    file(filename, 'wb').write(data)
    queue_id = db.add_to_queue(filename)
    response.status = 202
    response.header['Location'] = '/api/v1/queue/{0}'.format(queue_id)


@app.route('/api/v1/queue/<queue_id:int', method='GET')
def get_queue_status(queue_id):
    """get the status of the queue item"""
    queue_item = db.get_queue_item(queue_id)
    status = queue_item['status']
    if status != 'Done':
        return json.dumps({'status' : status})
    else:
        response.status = 303
        response.header['Location'] = '/api/v1/cleaned/{0}'.format(queue_item['name'])


if __name__ == '__main__':
    run(app, host='localhost', port='8000', reloader=True, debug=True)
