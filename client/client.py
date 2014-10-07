#!/usr/bin/env python
import os
import zipfile
import errno
import io
from lxml import etree

import docopt
from exercises_server_api import ExercisesServerSession

USAGE = '''
Usage:
    client.py <server> <port> read (<id> [<seed>])...
    client.py <server> <port> list

Options:
    read <id> [<seed>]: a list of ids and optional seeds can be given. If no
    seeds are specified, the template zip is returned, else an instance of the
    template is returned.
    list: returns a list of IDs available on the server.
'''


def mkdir_p(path):
    ''' mkdir -p functionality
    from:
    http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
    '''
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def write_template(templatezip, _id, _seed):
    '''
    Do required post processing of the template zip object and write to disk
    '''

    outputfolder = os.path.join('template', "{}-{}".format(_id[0:8], _seed))
    # make that folder if it does not exist
    mkdir_p(outputfolder)
    zf = io.BytesIO(templatezip)
    zipfile.ZipFile(zf).extractall(outputfolder)

    # read the xml file
    with open(os.path.join(outputfolder, 'main.xml')) as xml:
        mainxml = etree.XML(xml.read())


    elements_to_remove = ['response', 'hint']
    for elem in elements_to_remove:
        for thiselem in mainxml.findall(elem):
            thiselem.getparent().remove(thiselem)

    with open(os.path.join(outputfolder, 'main.xml'), 'w') as out:
        out.write(etree.tostring(mainxml, encoding='utf-8',
                                 xml_declaration=True))


if __name__ == "__main__":
    arguments = docopt.docopt(USAGE)
    server = arguments['<server>']
    port = arguments['<port>']
    session = ExercisesServerSession('{}:{}'.format(server, port), auth=None,
                                     verify=False)
    alltemplates = session.list('testing')
    # just list all the template IDs
    if arguments['list']:
        for template in alltemplates:
            print(template['id'])

    # get a template from the server
    if arguments['read']:
        all_ids = arguments['<id>']
        if arguments['<seed>']:
            all_seeds = arguments['<seed>']
        else:
            all_seeds = [None for i in all_ids]

        for _id, _seed in zip(all_ids, all_seeds):

            # if we're asking for a full id, just ask the server for it

            if len(_id) > 8:
                template = session.read(_id, 'testing', _seed)
            else:
                # if we're asking for a short id, first get the list of ids
                # from the server then select the correct one
                template = [t for t in alltemplates if t['id'].startswith(_id)]
                assert(len(template) == 1)
                template = template[0]
                longid = template['id']
                template = session.read(longid, 'testing', _seed)

            template = write_template(template, _id, _seed)
