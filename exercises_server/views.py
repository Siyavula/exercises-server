from pyramid.response import Response
from pyramid.exceptions import NotFound
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.view import view_config

from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm.attributes import instance_dict

import logging
log = logging.getLogger(__name__)

from .models import (
    DBSession,
    Exercise,
    CurrentVersion,
    )

from exercises_server.errors import ExerciseInvalid
from exercises_server.requests import log_request
from exercises_server.utils import parse_iso8601


@view_config(route_name='read', renderer='json')
def read_view(request):
    # {'id': str [required], 'version': str [None], 'rseed': int [None], 'branch': ('testing', 'published') ['published'], 'make_derivative': bool [False]}

    params = parse_json_body(
        request.json_body,
        required_keys = ['id'],
        optional_keys = ['version', 'random_seed', 'branch'],
        defaults = {'make_derivative': False})

    if params.has_key('version'):
        if params.has_key('branch'):
            raise HTTPBadRequest("JSON body may contain 'version' or 'branch' but not both")
        version = params['version']
    else:
        branch = params.get('branch', 'published')
        version = "select version from CurrentVersion where branch == params['branch'] and id == params['id']" # TODO

    exercise = "select data from Exercise where id == params['id'] and version == version" # TODO
    exercise = DBSession.query(Exercise).get(params['id'], version)
    if not exercise:
        raise NotFound()

    if params.has_key('random_seed'):
        # TODO
        if False: # exercise is static:
            raise HTTPBadRequest("Static exercise cannot have a random seed")
        # TODO: exercise = generate instance

    if params['make_derivative']:
        pass # TODO

    return {"exercise": exercise}


@view_config(route_name='update', renderer='json')
def update_view(request):
    log_request('Put entry', entry=request.matchdict['id'])

    params = parse_json_body(
        request.json_body,
        required_keys = ['data'])

    # TODO: question = question_from_zip(params['data'])
    id = question.id
    version = question.version

    entry = Entry.get_by_id(question.id, question.version)
    if not entry:
        try:
            entry = Entry.create(request.json_body['entry'], request.request_id)
        except ValueError as e:
            raise EntryInvalid(e.message)
        DBSession.add(entry)
        DBSession.flush()
        log.info("Created entry: %s" % entry)
    else:
        try:
            entry.update(params['data'])
        except ValueError as e:
            raise EntryInvalid(e.message)
        DBSession.add(entry)
        DBSession.flush()
        log.info("Updated entry: %s" % entry)
    return {"result": "success"}


'''
def create_view(request):
    log_request('Create entry')
    for key in 'user', 'entry':
        if not request.json_body.has_key(key):
            raise HTTPBadRequest('Missing required key: ' + key)
    return {"entry": entry}


@view_config(route_name='delete', renderer='json')
def delete_view(request):
    log_request('Delete entry', entry=request.matchdict['id'])
    for key in 'user':
        if not request.json_body.has_key(key):
            raise HTTPBadRequest('Missing required key: ' + key)
    entry = Entry.get_by_id(request.matchdict['id'])
    if not entry:
        raise NotFound()
    entry.delete(request.json_body['user'])
    DBSession.delete(entry)
    log.info("Deleted entry: %s" % entry)
    return {"entry": entry}


@view_config(route_name='list', renderer='json')
def list_view(request):
    query = DBSession.query(Entry)
    entries = query.order_by(Entry.created_at.desc()).all()
    return {"entries": entries}

'''
