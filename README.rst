Siyavula Exercises Server
=========================

This is a web server for managing Siyavula's repository of exercises
through a CRUD like interface.

Installation
------------

 * Setup a virtualenv: ``virtualenv --no-site-packages env``
 * Activate it: ``source env/bin/activate``
 * ``env/bin/pip install numpy``
 * ``python setup.py develop``
 * Clone and install dependencies
    * ``mkdir src ; cd src``

    * ``git clone https://github.com/Siyavula/cnxml-validator``
    * ``cd cnxml-validator``
    * ``../../env/bin/python setup.py develop``
    * ``cd ..``

    * ``git clone https://github.com/Siyavula/monassis-library``
    * ``cd monassis-library``
    * ``../../env/bin/python setup.py develop``
    * ``cd ..``

    * ``git clone https://github.com/Siyavula/siyavula.asciisvg``
    * ``cd siyavula.asciisvg``
    * ``../../env/bin/python setup.py develop``
    * ``cd ..``

    * ``git clone https://github.com/Siyavula/siyavula.transforms``
    * ``cd siyavula.transforms``
    * ``../../env/bin/python setup.py develop``
    * ``cd ..``

    * ``git clone https://github.com/sympy/sympy``
    * ``cd sympy``
    * ``../../env/bin/python setup.py install``
    * ``cd ..``

    * ``git clone https://github.com/mk-fg/yapps``
    * ``cd yapps``
    * ``../../env/bin/python setup.py install``
    * ``cd ..``

 * ``initialize_db development.ini``
 * ``pserve development.ini --reload``

To run functional and unittests, run: ``nosetests``
