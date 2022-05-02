.. highlight:: bash

To install the prerequisites for this example::

    pip install asphalt-web[starlette]

To start the ``static`` example::

    PYTHONPATH=. asphalt run config.yaml --service static

To start the ``dynamic`` example::

    PYTHONPATH=. asphalt run config.yaml --service dynamic

Then, navigate to http://localhost:8000 in your browser.
