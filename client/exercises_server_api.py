import requests, urlparse, json


class ExercisesServerException(Exception):
    def __init__(self, status_code, error_message):
        Exception.__init__(self, str(error_message) + ' [' + str(status_code) + ']')
        self.status_code = status_code
        self.error_message = error_message


class ValidationError(ExercisesServerException):
    def __init__(self, status_code, error_message, validation_result):
        ExercisesServerException.__init__(self, status_code, error_message)
        self.validation_result = validation_result

    def __str__(self):
        return ExercisesServerException.__str__(self) + ' ' + self.validation_result['exception'] + ' in ' + self.validation_result['phase'] + ' phase with random seed ' + repr(self.validation_result['random_seed'])


class UnhandledResponse(ExercisesServerException):
    pass


class ExercisesServerSession:
    def __init__(self, host_uri, auth=None, verify=True):
        self.host_uri = host_uri
        self.request_params = {
            'auth': auth,
            'verify': verify,
        }


    def __handle_unexpected_status_codes(self, response, known_codes=[200]):
        if response.status_code not in known_codes:
            try:
                message = json.loads(response.content)['error']['message']
            except Exception:
                message = None
            raise UnhandledResponse(response.status_code, message)


    def read(self, id, version=None, random_seed=None, make_derivative=None):
        json_data = {'id': str(id)}
        if version is not None:
            json_data['version'] = str(version)
        if random_seed is not None:
            json_data['random_seed'] = int(random_seed)
        if make_derivative is not None:
            json_data['make_derivative'] = bool(make_derivative)
        response = requests.get(
            urlparse.urljoin(self.host_uri, '/read'),
            data = json.dumps(json_data),
            **self.request_params)
        self.__handle_unexpected_status_codes(response)
        from base64 import b64decode
        return b64decode(json.loads(response.content)['exercise'])


    def insert_or_update(self, id, version, zipData):
        from base64 import b64encode
        response = requests.put(
            urlparse.urljoin(self.host_uri, '/update'),
            data = json.dumps({
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
        json_data = {'id': str(id)}
        if version is not None:
            json_data['version'] = str(version)
        if branch is not None:
            json_data['branch'] = str(branch)
        response = requests.put(
            urlparse.urljoin(self.host_uri, '/publish'),
            data = json.dumps(json_data),
            **self.request_params)
        self.__handle_unexpected_status_codes(response)
        assert json.loads(response.content)['result'] == 'success'


    def retract(self, id, branch=None):
        json_data = {'id': str(id)}
        if branch is not None:
            json_data['branch'] = str(branch)
        response = requests.put(
            urlparse.urljoin(self.host_uri, '/retract'),
            data = json.dumps(json_data),
            **self.request_params)
        self.__handle_unexpected_status_codes(response)
        assert json.loads(response.content)['result'] == 'success'


    def list(self, branch=None):
        json_data = {}
        if branch is not None:
            json_data['branch'] = branch
        response = requests.get(
            urlparse.urljoin(self.host_uri, '/list'),
            data = json.dumps(json_data),
            **self.request_params)
        self.__handle_unexpected_status_codes(response)
        return json.loads(response.content)['exercises']


if __name__ == '__main__':

    def template_id_to_uuid(iTemplateId):
        from uuid import uuid5, NAMESPACE_X500
        return uuid5(NAMESPACE_X500, '/monassis/template/' + str(iTemplateId))

    def make_zip(iPath):
        import os, zipfile, StringIO, subprocess
        # Get UUID
        with open(os.path.join(iPath, '__id__'), 'rt') as fp:
            templateId = template_id_to_uuid(int(fp.read().strip()))
        # Get version (last commit name)
        stdout, stderr = subprocess.Popen(['git', 'log', '-n', '1', '--pretty=oneline', '.'], cwd=iPath, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        templateVersion = stdout.strip().split()[0]
        # Build zip
        filenames = os.listdir(iPath)
        filenames.sort()
        zipBytes = StringIO.StringIO()
        zipArchive = zipfile.ZipFile(zipBytes, 'w', compression=zipfile.ZIP_DEFLATED)
        for filename in filenames:
            if filename in ['__id__']:
                continue
            zipArchive.write(os.path.join(iPath, filename), filename)
        zipArchive.close()
        zipBytes.seek(0)
        return templateId, templateVersion, zipBytes.read()

    # Connect
    session = ExercisesServerSession('http://localhost:6544', auth=None, verify=False)

    # List
    print 'Listing branches'
    print ' * default:  ', session.list()
    print ' * testing:  ', session.list('testing')
    print ' * published:', session.list('published')
    try:
        session.list('other')
        assert False
    except UnhandledResponse, error:
        assert error.status_code == 400

    # update
    print 'Validating and putting exercise'
    #path = '/home/carl/work/siyavula/code/monassis-templates-develop/mathematics/grade10/01-algebraic-expressions/01decToFrac'
    path = '/home/carl/work/siyavula/code/monassis-templates-develop/physical_sciences/grade12/06-doppler-effect/2_21_L1_L2_S_same_dir'
    exerciseId, exerciseVersion, exerciseData = make_zip(path)
    session.insert_or_update(exerciseId, exerciseVersion, exerciseData)

    # read
    print 'Reading back exercise'
    for version in ['testing', exerciseVersion]:
        print 'Read', version
        assert session.read(exerciseId, version=version) == exerciseData
    data = session.read(exerciseId, version=exerciseVersion, random_seed=1)
    with open('test.zip', 'wb') as fp:
        fp.write(data)

    # publish
    print 'Publishing'
    session.publish(exerciseId)
    assert session.read(exerciseId, version='published') == exerciseData

    # retract
    print 'Retracting'
    session.retract(exerciseId, branch='both')
