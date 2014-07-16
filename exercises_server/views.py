from pyramid.response import Response
from pyramid.exceptions import NotFound
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.view import view_config

from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm.attributes import instance_dict
import transaction

import logging
log = logging.getLogger(__name__)

from .models import (
    DBSession,
    Exercise,
    CurrentVersion,
    )

from exercises_server.errors import ExerciseInvalid, BadRequest
from exercises_server.requests import log_request
from exercises_server.utils import parse_iso8601, parse_json_body


@view_config(route_name='read', renderer='json')
def read_view(request):
    '''
    Read an exercise from the database and return it in a base-64
    encoded zip data stream.

    GET /read
        < {
            'id': str [required],                      # The id of the exercise to read
            'version': str [default: published],       # The version number or branch head of the exercise to read
            'random_seed': int, [optional]             # The random seed, if this exercise is a template and you want an instance of it
            'make_derivative': bool [default: False],  # Whether to add the derived-from element to the exercise metadata
        }
        > { 'exercise': zip_data }
          HTTPNotFound
          HTTPBadRequest (ExeciseInvalid, BadRequest)
    '''
    params = parse_json_body(
        request.json_body,
        required_keys = ['id'],
        optional_keys = ['random_seed'],
        defaults = {'version': 'published', 'make_derivative': False})

    assert not params['make_derivative'], "TODO: derivatives not yet implemented"

    version = params['version']
    if version in ['testing', 'published']:
        result = DBSession.query(CurrentVersion).get((version, params['id']))
        if not result:
            raise NotFound("Exercise %s is not on the %s branch" % (params['id'], params['version']))
        version = result.version

    exercise = DBSession.query(Exercise).get((params['id'], version))
    if not exercise:
        raise NotFound("Exercise %s with version %s not found" % (params['id'], version))

    if params.has_key('random_seed'):
        randomSeed = int(params['random_seed'])

        # TODO: Check that this is a template and not a static exercise
        if False:
            raise ExeciseInvalid("Static exercise cannot have a random seed")

        # Generate instance from template
        from monassis.qnxmlservice import question_from_zip
        question = question_from_zip(exercise.data, iRandomSeed=randomSeed)
        
        if params['make_derivative']:
            pass # TODO

        # Zip instance up again
        import zipfile, StringIO
        zipBytes = StringIO.StringIO()
        zipArchive = zipfile.ZipFile(zipBytes, 'w', compression=zipfile.ZIP_DEFLATED)
        zipArchive.writestr('main.xml', question.as_xml())
        for filename, data in question.files.iteritems():
            zipArchive.writestr(filename, data)
        zipArchive.close()
        zipBytes.seek(0)
        exerciseZip = zipBytes.read()
    else:
        exerciseZip = exercise.data
        if params['make_derivative']:
            pass # TODO

    from base64 import b64encode
    return {"exercise": b64encode(exerciseZip)}


@view_config(route_name='update', renderer='json')
def update_view(request):
    '''
    Validate an exercise and update or insert it in the database. Set
    the testing branch head to point to this version of the exercise.

    PUT /update
        < {
            'id': str [required],                    # The id of the exercise to save or update
            'version': str [required],               # The version of the exercise to save or update
            'data_base64': base-64 encoded zip data  # Base-64 encoded data to save
        }
        > { 'result': 'success' }
    '''
    params = parse_json_body(
        request.json_body,
        required_keys = ['id', 'version', 'data_base64'])
    log_request('update', id=params['id'], version=params['version'])

    from base64 import b64decode
    data = b64decode(request.json_body['data_base64'])

    # TODO: validate exercise/template

    from utils import now_utc
    exercise = DBSession.merge(Exercise(id=params['id'], version=params['version'], data=data, last_updated=now_utc()))
    log.info("Put exercise: %s" % exercise)
    currentVersion = DBSession.merge(CurrentVersion(branch='testing', id=params['id'], version=params['version']))
    log.info("Updated branch head: %s" % currentVersion)
    transaction.commit()

    return {"result": "success"}


@view_config(route_name='publish', renderer='json')
def publish_view(request):
    '''
    Set the published branch head to point to a given version of an
    exercise.

    PUT /publish
        < {
            'id': str [required],               # The id of the exercise to publish
            'version': str [default: testing],  # The version number or branch head of the exercise to publish
            'branch': ('testing', 'published'), [default: published]  # Set this to 'testing' to update the testing branch head instead
        }
        > { 'result': 'success' }
    '''
    params = parse_json_body(
        request.json_body,
        required_keys = ['id'],
        defaults = {'version': 'testing', 'branch': 'published'})
    if params['branch'] not in ['testing', 'published']:
        raise HTTPBadRequest("Unknown branch %s should be 'testing' or 'published'" % (repr(params['branch'])))

    log_request('Publish entry', entry=params.get('id'))

    version = params['version']
    if version in ['testing', 'published']:
        result = DBSession.query(CurrentVersion).get((version, params['id']))
        if not result:
            raise NotFound("Exercise %s is not on the %s branch" % (params['id'], params['version']))
        version = result.version

    entry = Exercise.get_by_id(params['id'], version)
    if not entry:
        raise NotFound("Exercise with id %s and version %s not found" % (str(params['id']), str(version)))

    currentVersion = DBSession.merge(CurrentVersion(branch=params['branch'], id=params['id'], version=version))
    log.info("Updated branch head: %s" % currentVersion)
    transaction.commit()

    return {"result": "success"}


@view_config(route_name='retract', renderer='json')
def retract_view(request):
    '''
    Remove an exercise from the published branch or both testing and
    published.

    PUT /retract
        < {
            'id': str [required],                                  # The id of the exercise to retract
            'branch': ('published', 'both'), [default: published]  # The branch(es) from which to retract
        }
        > { 'result': 'success' }
    '''
    params = parse_json_body(
        request.json_body,
        required_keys = ['id'],
        defaults = {'branch': 'published'})

    if params['branch'] == 'published':
        branches = ['published']
    elif params['branch'] == 'both':
        branches = ['testing', 'published']
    else:
        raise HTTPBadRequest("Unknown branch %s should be 'published' or 'both'" % (repr(params['branch'])))

    log_request('Retract entry', entry=params.get('id'))

    for branch in branches:
        currentVersion = CurrentVersion.get_by_id(branch, params['id'])
        if currentVersion:
            DBSession.delete(currentVersion)
            log.info("Retracted branch head: %s" % currentVersion)

    return {"result": "success"}


@view_config(route_name='list', renderer='json')
def list_view(request):
    '''
    Return a list of all exercise ids available on the given branch.

    GET /list
        < {
            'branch': ('testing', 'published'), [default: published]  # The branch to list
        }
        > { 'exercises': [exercise_id, ... ] }
    '''
    params = parse_json_body(
        request.json_body,
        defaults = {'branch': 'published'})

    if params['branch'] not in ['testing', 'published']:
        raise HTTPBadRequest("Unknown branch %s should be 'testing' or 'published'" % (repr(params['branch'])))

    query = DBSession.query(CurrentVersion.id).filter(CurrentVersion.branch == params['branch'])
    exercises = [id for (id,) in query]
    return {"exercises": exercises}
