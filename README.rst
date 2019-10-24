Python wrapper for the Alpine API
=================================

Welcome to the official Python library for the Alpine API. In this first release we've focused on a subset of the full
API that we feel users will most frequently use.

This library can be used to automate, add, or simplify functionality of Alpine.

Documentation (and examples):
   http://python-alpine-api.readthedocs.io/

Source code:
   https://github.com/AlpineNow/python-alpine-api

Python Package Index:
   https://pypi.python.org/pypi/alpine

Setup:
   Execute command::

      pip install alpine

Requirements:
   Using this package requires access to a TIBCO Team Studio instance. For more information, see the TIBCO Team Studio homepage:
   https://community.tibco.com/products/tibco-data-science

License:
   We use the MIT license. See the LICENSE file on GitHub for details.

Example
=======

Running a workflow and downloading the results::

    >>> import alpine as AlpineAPI
    >>> session = AlpineAPI.APIClient(host, port, username, password)
    >>> process_id = session.workfile.process.run(workfile_id)
    >>> session.workfile.process.wait_until_finished(workfile_id, process_id)
    >>> results = session.workfile.process.download_results(workfile_id, process_id)

