import transaction

from pyramid.paster import get_appsettings

import exercises_server.requests
from exercises_server.models.support import DBSession
from exercises_server.models import Base, Exercise, CurrentVersion

def init_testing_app():
    from exercises_server import main
    from webtest import TestApp

    app = main({}, **get_appsettings('test.ini#main'))
    return TestApp(app)


def init_testing_db():
    # NOTE: init_testing_app must have been called first
    Base.metadata.create_all()
    return DBSession()
