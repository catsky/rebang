import sae

import tornado.wsgi

from view import urls as view_url

settings = {
    #"debug" : True,
}

app = tornado.wsgi.WSGIApplication( view_url, **settings)

application = sae.create_wsgi_app(app)


