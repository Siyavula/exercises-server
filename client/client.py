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

if __name__ == "__main__":
    arguments = docopt.docopt(USAGE)
    server = arguments['<server>']
    port = arguments['<port>']
    session = ExercisesServerSession('{}:{}'.format(server, port), auth=None,
                                     verify=False)
    # just list all the template IDs
    if arguments['list']:
        templates = session.list('testing')
        for template in templates:
            print(template['id'])

    # get a template from the server
    if arguments['read']:
        all_ids = arguments['<id>']
        if arguments['<seed>']:
            all_seeds = arguments['<seed>']
        else:
            all_seeds = [None for i in all_ids]

        for _id, _seed in zip(all_ids, all_seeds):
            template = session.read(_id, 'testing', _seed)
            with open("{}.zip".format(_id), 'wb') as out:
                print("Writing {}".format(_id))
                out.write(template)