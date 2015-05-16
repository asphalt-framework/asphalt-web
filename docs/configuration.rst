Configuration
=============

At minimum, the WAMP client configuration needs to know where to connect
The general structure of the configuration is as follows:

.. code-block:: yaml

    session:
      context_var: dbsession
      commit_on_finish: false
      # add keyword arguments to sessionmaker() here
    engines:
      db1:
        url: "postgresql:///mydatabase"
        metadata: package.foo:Base.metadata
        # add keyword arguments to create_engine() here
      db2:
        url: "sqlite:///mydb.sqlite"
        metadata: otherpackage.bar:Base.metadata
        # add keyword arguments to create_engine() here



Configuration options
---------------------

Top level component options:

================== =============================================== ==============================
Option             Description                                     Default value
================== =============================================== ==============================
engines            Dictionary of engine configurations
session            Dictionary of session configuration options
                   (see below)
================== =============================================== ==============================

Session configuration options:

===================== ================================================ ==========================
Option                  Description                                    Default value
===================== ================================================ ==========================
context_var           Attribute name for the session in the context    dbsession
commit_on_finish      Whether to automatically commit the session       ``True``
                      when a request level context is finished,
                      assuming that no exception was raised
(anything else)       Keyword arguments passed to `sessionmaker`_
===================== ================================================ ==========================




Each engine configuration item can be one of the following:

* a `connection URL`_
* a dictionary of engine options and other keyword arguments to be passed to `create_engine()`_
* an ``Engine`` or ``Connection`` instance

If only a single database has been specified, the engine will be directly bound to the session, and
you won't have to provide any metadata to use the session.

In order to use the session with more than one database, the mapped classes belonging to each
database must inherit from a base class specific to the database. This is because the extension
binds the engines to the database specific ``MetaData`` objects which you need to specify in the
engine configuration as the ``metadata`` option. The value can be a textual reference like
package:variable-path or an actual ``MetaData`` instance. If you don't need sessions, you can omit
the ``metadata`` option entirely.

The session factory (sessionmaker) object can be provided in the context for the purposes of adding
event listeners to it, but this requires explicitly setting the ``sessionmaker_property`` to a
legal value (such as "sessionmaker") in the session configuration options.

It is also possible to prevent the session property from showing in the context by specifying
an empty string as the value of ``session_property``.

.. code:: yaml

    components:
      sqlalchemy:
        engines:
          db:
            url: "postgresql:///mydatabase"

This example assumes that you have a PostgreSQL database named "mydatabase" that you're accessing
via the default UNIX domain socket. The engine will be accessible as ``ctx.db`` and the session
as ``ctx.dbsession``.

.. code:: yaml

    components:
      sqlalchemy:
        engines:
          db1:
            url: "postgresql:///mydatabase"
            metadata: "package.foo:Base.metadata"
          db2:
            url: "sqlite:///mydb.sqlite"
            metadata: "otherpackage.bar:Base.metadata"

This example configures two databases. The first will be available as ``ctx.db1`` and the other as
``ctx.db2``. The session will still be ``ctx.dbsession`` as usual. The metadata object for the
first database is located on the package ``package.foo``, in the ``metadata`` property of the
``Base`` class.

.. code:: yaml

    components:
      sqlalchemy:
        session:
          session_property: session
          commit_on_finish: false
        engines:
          db: "postgresql:///mydatabase"

This example changes some session options from the default. It disables the automatic commit at the
end of every request, and it changes the session property name so it is now accessed as
``ctx.session`` instead of ``ctx.dbsession``.


Using the session with request level contexts
---------------------------------------------

.. code:: python

  def some_request_handler(ctx):
      return ctx.dbsession.query(SomeClass).first()


Using the session in application start/finish callbacks
-------------------------------------------------------

Since sessions are supposed to be short lived, the ``dbsession`` context property returns a context
managed session instead:

.. code:: python

  def app_startup(ctx):
      with ctx.dbsession as session:
          # The session will by default automatically commit at the end of the with block unless an
          # exception was raised
          session.add(SomeClass())

.. _connection URL: http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls
.. _sessionmaker: http://docs.sqlalchemy.org/en/latest/orm/session_api.html#sqlalchemy.orm.session.sessionmaker
.. _create_engine(): http://docs.sqlalchemy.org/en/latest/core/engines.html#sqlalchemy.create_engine
