import io

import cherrypy

import config


class ImageResponse(object):
    @cherrypy.expose
    def index(self, id=''):
        if id == '':
            return ''
        cherrypy.response.headers['Content-Type'] = "image/png"
        f = io.open('/root/profile_pics/%s' % (id), 'rb')
        return cherrypy.lib.file_generator(f)

    @cherrypy.expose
    def original(self, id=''):
        if id == '':
            return ''
        cherrypy.response.headers['Content-Type'] = "image/png"
        f = io.open('/root/profile_pics/originals/%s' % (id), 'rb')
        return cherrypy.lib.file_generator(f)

cherrypy.config.update({
    'server.socket_host': config.WEBHOOK_HOST,
    'server.socket_port': config.IMAGES_PORT,
})

cherrypy.quickstart(ImageResponse())
