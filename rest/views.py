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
    Entry,
    )

from rest.errors import EntryInvalid, EntryLocked
from rest.requests import log_request
from rest.utils import parse_iso8601


@view_config(route_name='create', renderer='json')
def create_view(request):
    log_request('Create entry')
    for key in 'user', 'entry':
        if not request.json_body.has_key(key):
            raise HTTPBadRequest('Missing required key: ' + key)
    try:
        entry = Entry.create(request.json_body['entry'], request.request_id)
    except ValueError as e:
        raise EntryInvalid(e.message)
    DBSession.add(entry)
    DBSession.flush()
    log.info("Created entry: %s" % entry)
    return {"entry": entry}


@view_config(route_name='read', renderer='json')
def read_view(request):
    entry = DBSession.query(Entry).get(request.matchdict['id'])
    if not entry:
        raise NotFound()
    return {"entry": entry}


@view_config(route_name='update', renderer='json')
def update_view(request):
    log_request('Update entry', entry=request.matchdict['id'])
    for key in 'user', 'entry':
        if not request.json_body.has_key(key):
            raise HTTPBadRequest('Missing required key: ' + key)
    entry = Entry.get_by_id(request.matchdict['id'])
    if not entry:
        raise NotFound()
    try:
        entry.update(request.json_body['user'], request.json_body['entry'], request.request_id)
    except ValueError as e:
        raise EntryInvalid(e.message)
    DBSession.add(entry)
    log.info("Updated entry: %s" % entry)
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


@view_config(route_name='lock', renderer='json')
def lock_view(request):
    log_request('Lock entry', entry=request.matchdict['id'])
    for key in 'user':
        if not request.json_body.has_key(key):
            raise HTTPBadRequest('Missing required key: ' + key)
    entry = Entry.get_by_id(request.matchdict['id'])
    if not entry:
        raise NotFound()
    entry.lock(request.json_body['user'], request.request_id)
    DBSession.add(entry)
    log.info("Locked entry: %s" % entry)
    return {"entry": entry}


@view_config(route_name='unlock', renderer='json')
def lock_view(request):
    log_request('Unlock entry', entry=request.matchdict['id'])
    for key in 'user':
        if not request.json_body.has_key(key):
            raise HTTPBadRequest('Missing required key: ' + key)
    entry = Entry.get_by_id(request.matchdict['id'])
    if not entry:
        raise NotFound()
    entry.unlock(request.json_body['user'])
    DBSession.add(entry)
    log.info("Unlocked entry: %s" % entry)
    return {"entry": entry}
