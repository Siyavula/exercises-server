import logging


def main(global_config, **settings):
    """
    This function returns a Pyramid WSGI application.
    """
    # This must be done before new relic
    setup_logging()

    # This should be done before any pyramid imports if possible,
    # certainly before make_wsgi_app()
    setup_newrelic(settings.get('newrelic.environment'))

    setup_database(settings)

    from pyramid.config import Configurator
    config = Configurator(settings=settings)

    setup_routes(config)

    config.scan()
    return config.make_wsgi_app()

def setup_routes(config):
    config.add_route('create',  '/create',      request_method='POST')
    config.add_route('read',    '/read/{id}',   request_method='GET')
    config.add_route('update',  '/update/{id}', request_method='PUT')
    config.add_route('delete',  '/delete/{id}', request_method='DELETE')
    config.add_route('list',    '/list',        request_method='GET')
    config.add_route('lock',    '/lock/{id}',   request_method='PUT')
    config.add_route('unlock',  '/unlock/{id}', request_method='PUT')


def setup_database(settings):
    from sqlalchemy import engine_from_config
    from rest.models import DBSession, Base

    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine


def setup_logging():
    """
    Attach the request-id aware filter to the first handler
    in the chain. This isn't ideal, but the logging config
    doesn't give us an easy way to attach filters to via a config
    file.
    """
    handler = logging.getLogger().handlers[0]

    # the nose test handlers mess with this
    if not handler.__module__.startswith('nose'):
        import rest.requests
        handler.addFilter(rest.requests.RequestIdFilter())
        # force the formatter to use a request id
        if handler.formatter:
            setattr(handler.formatter, '_fmt', '%(asctime)s %(levelname)-5.5s [%(requestid)s] [%(process)d] [%(name)s][%(threadName)s] %(message)s')


def setup_newrelic(env=None):
    """ If +env+ is not None, setup newrelic and tell
    it to use that environment config. """
    if env:
        import newrelic.agent
        newrelic.agent.initialize('newrelic.ini', env)
