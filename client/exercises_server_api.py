import requests
import urlparse
import json


class ExercisesServerException(Exception):
    '''
    Base class for all exercise server exceptions. In addition to the
    usual Exception attributes, this class exposes:

    status_code - the HTTP code returned by the exercises server

    error_message - the error message returned by the exercises server
    '''
    def __init__(self, status_code, error_message):
        Exception.__init__(self, str(error_message) + ' [' + str(status_code) + ']')
        self.status_code = status_code
        self.error_message = error_message


class ValidationError(ExercisesServerException):
    '''
    Raised when an exercise failed to validate. The validation_result
    attribute is a dict with the following keys:

    'exception' - the exception raised during validation

    'phase' - the testing phase during which the exception was
        raised, one of:

        'generation' - while generating the XML from a template

        'validation' - while validating the XML against the spec

        'type/marks/correct/input count' - while checking that there
            are matching numbers of <type>, <marks>, <correct>,
            <input> elements

        'correct response' - while checking that the correct
            response is marked as correct

        'html transform' - while transform the XML to HTML
    '''
    def __init__(self, status_code, error_message, validation_result):
        ExercisesServerException.__init__(self, status_code, error_message)
        self.validation_result = validation_result

    def __str__(self):
        return ExercisesServerException.__str__(self) + ' ' + self.validation_result['exception'] + ' in ' + self.validation_result['phase'] + ' phase with random seed ' + repr(self.validation_result['random_seed'])


class NotFound(ExercisesServerException):
    '''
    Raised when a HTTP 404 Not Found response is received.
    '''
    pass


class UnhandledResponse(ExercisesServerException):
    '''
    Unknown error. See status_code and error_message in
    ExercisesServerException for details.
    '''
    pass


class ExercisesServerSession:
    '''
    Class for setting up a session with the exercises server and
    making requests.
    '''

    def __init__(self, host_uri, auth=None, verify=True):
        '''
        Create a new exercises server session.

        host_uri - The URI of the exercises server with which to
            connect.

        auth - The username and password for HTTP authentication (if
            any), given as a tuple (username, password).

        verify - Whether to verify the signature of an HTTPS connect,
            if one is being made. Ignore for non-secure connections.
        '''
        self.host_uri = host_uri
        self.request_params = {
            'auth': auth,
            'verify': verify,
        }

    def __handle_unexpected_status_codes(self, response, known_codes=[200]):
        '''
        Internal method to check for expected response status codes
        and raise an exception on unexpected codes.
        '''
        if response.status_code not in known_codes:
            try:
                message = json.loads(response.content)['error']['message']
            except Exception:
                message = None
            raise UnhandledResponse(response.status_code, message)

    def read(self, id, version=None, random_seed=None, make_derivative=None):
        '''
        Read an exercise zip from the server.

        id - The id of the exercise to read.

        version - The version number of the exercise to read. Default:
            latest published version. This must be 'published',
            'testing' or a valid version number.

        random_seed - If the exercise is a template, the random seed
            for which to generate an instance. This must not be
            specified if the exercise is static (not a template).
            Default: return the template and not an instance of it.

        make_derivative - Whether to inject the derived-from headers
            into the exercise XML. Default: False. NOT YET IMPLEMENTED.

        Returns a binary string with the exercise zip.

        Raises NotFound if the specified exercise was not found.
        '''
        json_data = {'id': str(id)}
        if version is not None:
            json_data['version'] = str(version)
        if random_seed is not None:
            json_data['random_seed'] = int(random_seed)
        if make_derivative is not None:
            json_data['make_derivative'] = bool(make_derivative)
        response = requests.get(
            urlparse.urljoin(self.host_uri, '/read'),
            data=json.dumps(json_data),
            **self.request_params)
        self.__handle_unexpected_status_codes(response, [200, 404])
        if response.status_code == 404:
            raise NotFound(response.status_code, "Exercise not found")
        from base64 import b64decode
        return b64decode(json.loads(response.content)['exercise'])

    def insert_or_update(self, id, version, zipData):
        '''
        Put an exercise to the server (create or replace existing).

        id - The id of the exercise to put.

        version - The version number of the exercise to put.

        zipData - The binary string of exercise zip data.

        If an exercise with the given id and version already exists,
        it will be replaced; otherwise it will be created.

        Raises ValidationError if the exercise failed to validate.
        '''
        from base64 import b64encode
        response = requests.put(
            urlparse.urljoin(self.host_uri, '/update'),
            data=json.dumps({
                'id': str(id),
                'version': str(version),
                'data_base64': b64encode(zipData)}),
            **self.request_params)
        self.__handle_unexpected_status_codes(response, [200, 400])
        if response.status_code == 400:
            body = response.json()
            raise ValidationError(response.status_code, body['error']['message'], body['error']['validation_result'])
        assert json.loads(response.content)['result'] == 'success'

    def publish(self, id, version=None, branch=None):
        '''
        Set an existing exercise to be the published version of the
        exercise. Future read requests on this exercise id will return
        this version of the exercise by default.

        id - The id of the exercise to publish.

        version - The version number of the exercise to publish. This
            must be 'published', 'testing' or a valid version
            number. Note that setting this to 'published' will achieve
            nothing.

        branch - The branch to which to publish, one of 'published' or
            'testing'. Default: 'published'.
        '''
        json_data = {'id': str(id)}
        if version is not None:
            json_data['version'] = str(version)
        if branch is not None:
            json_data['branch'] = str(branch)
        response = requests.put(
            urlparse.urljoin(self.host_uri, '/publish'),
            data=json.dumps(json_data),
            **self.request_params)
        self.__handle_unexpected_status_codes(response)
        assert json.loads(response.content)['result'] == 'success'

    def retract(self, id, branch=None):
        '''
        Remove a published exercise. Future read requests on this
        exercise id will return a not found error by default (unless a
        version number is specified).

        id - The id of the exercise to retract.

        branch - The branch(es) from which to retract, one of 'published'
            or 'both'. Default: 'published'.
        '''
        json_data = {'id': str(id)}
        if branch is not None:
            json_data['branch'] = str(branch)
        response = requests.put(
            urlparse.urljoin(self.host_uri, '/retract'),
            data=json.dumps(json_data),
            **self.request_params)
        self.__handle_unexpected_status_codes(response)
        assert json.loads(response.content)['result'] == 'success'

    def list(self, branch=None):
        '''
        Get a list of all exercise ids available, along with their
        version numbers.

        branch - The branch from which to read exercise ids, one of
            'published' or 'testing'. Default: 'published'.

        Returns a list of dicts, where each dict has 'id' and
        'version' keys.
        '''
        json_data = {}
        if branch is not None:
            json_data['branch'] = branch
        response = requests.get(
            urlparse.urljoin(self.host_uri, '/list'),
            data=json.dumps(json_data),
            **self.request_params)
        self.__handle_unexpected_status_codes(response)
        return json.loads(response.content)['exercises']


if __name__ == '__main__':

    def template_id_to_uuid(iTemplateId):
        from uuid import uuid5, NAMESPACE_X500
        return uuid5(NAMESPACE_X500, '/monassis/template/' + str(iTemplateId))

    # Connect
    session = ExercisesServerSession('http://localhost:6544', auth=None, verify=False)

    # List
    print 'Listing branches'
    print ' * testing:  ', session.list('testing')
    print ' * published:', session.list('published')
    assert session.list() == session.list('published')
    try:
        session.list('other')
        assert False
    except UnhandledResponse, error:
        assert error.status_code == 400

    # update
    print 'Validating and putting exercise'
    exerciseId = '8acca24b-4461-593c-ba11-364e958eba78'
    exerciseVersion = '97b4e5bebfc2be2a8a03383def469deee399ac58'
    with open('test.zip', 'rb') as fp:
        exerciseData = fp.read()
    session.insert_or_update(exerciseId, exerciseVersion, exerciseData)

    # read
    print 'Reading back exercise'
    for version in ['testing', exerciseVersion]:
        print 'Read', version
        assert session.read(exerciseId, version=version) == exerciseData

    try:
        session.read(exerciseId, random_seed=123)
    except NotFound:
        pass
    else:
        assert False

    # publish
    print 'Publishing'
    session.publish(exerciseId)
    assert session.read(exerciseId, version='published') == exerciseData
    session.read(exerciseId, random_seed=123)

    print 'Listing branches'
    print ' * testing:  ', session.list('testing')
    print ' * published:', session.list('published')

    # retract
    print 'Retracting from published'
    session.retract(exerciseId)

    try:
        session.read(exerciseId, random_seed=123)
    except NotFound:
        pass
    else:
        assert False

    print 'Listing branches'
    print ' * testing:  ', session.list('testing')
    print ' * published:', session.list('published')

    print 'Retracting from both'
    session.retract(exerciseId, branch='both')

    print 'Listing branches'
    print ' * testing:  ', session.list('testing')
    print ' * published:', session.list('published')
