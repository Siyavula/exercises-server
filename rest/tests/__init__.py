import transaction

from pyramid.paster import get_appsettings

import rest.requests
from rest.models.support import DBSession
from rest.models import Base, Entry

def init_testing_app():
    from rest import main
    from webtest import TestApp

    app = main({}, **get_appsettings('test.ini#main'))
    return TestApp(app)


def init_testing_db():
    # NOTE: init_testing_app must have been called first
    Base.metadata.create_all()
    return DBSession()
