Developing shoobx.rml2odt
=========================

We appreciate both bug reports and merge requests. Don't be dissuaded if
it takes a long time for us to answer, it just means we are busy with other
things.

We loosely follow PEP8 style conventions.


Development requirements
------------------------

* Python 2.7, 3.5 and 3.6, with pip for all those versions.

* Libreoffice 3.5 or higher.

* Tox: https://tox.readthedocs.io/en/latest/

* Ghostscript


Running tests
-------------

``$ tox -e py27``


macOS
-----

We recommend you install homebrew::

    ``/usr/bin/ruby -e “$(curl -fsSL https://raw.githibusercontent.com/Homebrew/install/master/install)”``

Then install unoconv with homebrew:

    ``$ brew install ghoststcript``

    ``$ brew install unoconv``

    ``$ ln -s /usr/local/Cellar/unoconv/0.7/bin/unoconv /usr/local/bin/unoconv``
