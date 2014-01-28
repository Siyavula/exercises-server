Generic REST service README
===========================

This is a Pylons-based framework for a generic REST web server that
supports CRUD through HTTP POST, GET, PUT, DELETE.

Development
-----------

 * Setup a virtualenv: ``virtualenv --no-site-packages env``
 * Activate it: ``source env/bin/activate``
 * ``python setup.py develop``
 * ``initialize_db development.ini``
 * ``pserve development.ini --reload``

To run functional and unittests, run: ``nosetests``

Production
----------

The API uses HTTP basic authentication and must be accessed over SSL:

 * username: USERNAME
 * password: PASSWORD

The SSL certificate is self-signed, so a browser will complain that it
doesn't look legitimate.  That's okay, we're only using it to secure
the communication, not verify each party.

The recommended production setup is to use a combination of nginx and
gunicorn. Nginx is the frontend and handles badly behaved clients, SSL
and HTTP Basic authentication. It proxies requests to a collection of
gunicorn servers on the local host.

Setup
~~~~~

First, setup the basics.

 * ensure Python and pip are installed using the normal means
 * ensure virtualenv is installed:
   ``pip install virtualenv``
 * install git and other dependencies:
   ``sudo apt-get install libpq-dev python-dev git``

Setup the postgres database:

- use normal procedure here
- create the ``rest`` database and ``rest`` user.

Then create the rest user and clone the repo.

- ``sudo useradd -d /home/rest -m rest``
- ``sudo su - rest``
- ``git clone https://github.com/Siyavula/generic-rest-service.git``
- ``cd generic-rest-service``
- ``git checkout develop``
- ``mkdir log``

Setup the environment:

- ``virtualenv --no-site-packages env``
- ``source env/bin/activate``
- ``python setup.py develop``

If this is the first time the database has been setup, run:

- ``initialize_db production.ini``

nginx
~~~~~

Install nginx:

``sudo apt-get install nginx``

Link in the rest config:

``sudo ln -s /home/rest/generic-rest-service/resources/nginx/rest.conf /etc/nginx/sites-enabled/``

And restart nginx:

``sudo service nginx restart``

upstart
~~~~~~~

Tell upstart about the REST gunicorn server:

``sudo ln -s /home/rest/generic-rest-service/resources/upstart/rest.conf /etc/init/``
``sudo initctl reload-configuration``

And start it:

``sudo start rest``

Logging
~~~~~~~

nginx's production logs are in ``~rest/log/access.log``

The rest application logs are in ``~rest/log/rest.log``

Deploying changes
~~~~~~~~~~~~~~~~~

To deploy changes to the service,

- make the changes elsewhere and commit to git
- ``git pull`` on the production server
- tell upstart to restart rest: ``sudo restart rest``

If you have made changes to the nginx config, you'll need to restart nginx too:

``sudo service nginx restart``

IP Whitelisting
~~~~~~~~~~~~~~~

See ``resources/nginx/rest.conf`` for info on how to whitelist IPs.
