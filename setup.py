import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()

requires = [
    'pyramid == 1.4',
    'python-dateutil == 2.1',
    'SQLAlchemy',
    'transaction',
    'pyramid_tm',
    'pyramid_debugtoolbar',
    'zope.sqlalchemy',
    'waitress',
    'newrelic',
    'psycopg2',
    'gunicorn',
    'nose',
    'webtest',
    ]

setup(name='rest',
      version='0.0',
      description='Generic REST service',
      long_description=README,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='Carl Scheffler',
      author_email='carl@siyavula.com',
      url='',
      keywords='web wsgi bfg pylons pyramid',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='rest',
      install_requires=requires,
      entry_points="""\
      [paste.app_factory]
      main = rest:main
      [console_scripts]
      initialize_db = rest.scripts.initializedb:main
      """,
      )
