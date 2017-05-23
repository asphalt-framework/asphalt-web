from pathlib import Path

from setuptools import setup

setup(
    name='asphalt-web',
    use_scm_version={
        'version_scheme': 'post-release',
        'local_scheme': 'dirty-tag'
    },
    description='Web application component for the Asphalt framework',
    long_description=Path(__file__).with_name('README.rst').read_text('utf-8'),
    author='Alex Grönholm',
    author_email='alex.gronholm@nextday.fi',
    url='https://github.com/asphalt-framework/asphalt-web',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ],
    license='Apache License 2.0',
    zip_safe=False,
    packages=[
        'asphalt.web',
        'asphalt.web.rpc',
        'asphalt.web.rpc.xmlrpc',
        'asphalt.web.servers',
        'asphalt.web.session',
        'asphalt.web.session.stores'
    ],
    setup_requires=[
        'setuptools_scm >= 1.7.0'
    ],
    install_requires=[
        'asphalt ~= 3.0',
        'asphalt-templating ~= 2.0',
        'asphalt-serialization ~= 4.0',
        'h11 == 0.7.0',
        'multidict ~= 2.1',
        'wsproto == 0.9'
    ],
    extras_require={
        'fastcgi': ['fcgiproto ~= 1.0'],
        'mongodb': ['asphalt-mongodb ~= 1.0'],
        'sqlalchemy': ['asphalt-sqlalchemy ~= 2.0'],
        'xmlrpc': ['defusedxml >= 0.4.1'],
        'testing': [
            'pytest',
            'pytest-cov',
            'pytest-catchlog',
            'pytest-asyncio >= 0.5.0',
            'lxml',
        ]
    },
    entry_points={
        'asphalt.components': [
            'web = asphalt.web.component:WebServerComponent'
        ],
        'asphalt.web.servers': [
            'fastcgi = asphalt.web.servers.fastcgi:FastCGIProtocol [fastcgi]',
            'http = asphalt.web.servers.http:HTTPProtocol [http]'
        ],
        'asphalt.web.sessionstores': [
            'memory = asphalt.web.session.stores.memory:MemorySessionStore',
            'mongodb = asphalt.web.session.stores.mongodb:MongoDBSessionStore [mongodb]',
            ('sqlalchemy = asphalt.web.session.stores.sqlalchemy:SQLAlchemySessionStore '
             '[sqlalchemy]')
        ]
    }
)
