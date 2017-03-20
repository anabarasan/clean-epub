#!/usr/bin/env python
"""
app.py
server side for cleaning a epub file.
    uploading a epub file
    removing the span tags
    repackage and deliver to user
"""
# Standard Library
import os

# Bottle
from bottle import Bottle, error, HTTPError, request, response, run


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
    file(epub.filename, 'wb').write(data)
    response.status = 202
    # @TODO start the conversion process and return 202 with queue location


if __name__ == '__main__':
    run(app, host='localhost', port='8000', reloader=True, debug=True)
