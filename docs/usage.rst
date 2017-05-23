User guide
==========

Simple "Hello, World!"::

    def handler(ctx):
        # No need for "async def" if you don't need "await", "async for" or "async with"
        return 'Hello, World!'

Render a template to the output::

    def handler(ctx):
        # Assumes the presence of a template renderer resource with the name "default"
        # The template has two variables it can use here: "ctx" and "foo"
        return ctx.response.render_template('example.html', {'foo': 'bar'})

Send a file using the most efficient method allowed by the configuration::

    def handler(ctx):
        # This is an absolute filesystem path
        return ctx.response.send_file('/data/files/dvdimages/bigdata.iso')

Send a dictionary serialized as JSON::

    def handler(ctx):
        # Assumes the presence of a serializer resource with the name "json"
        data = {'hello': 'world'}
        return ctx.response.serialize(data, 'json')

Send an error response::

    def handler(ctx):
        return ctx.response.send_error(404, 'Nothing to see here!')

Receive a submitted form (a ``POST`` response)::

    async def handler(ctx):
        # "form" will be a multidict.MultiDict
        form = await ctx.request.get_form()
        return 'Your age is {age}, sex is {sex} and nationality is {nationality}'.format(**form)

Efficiently receive uploaded files::

    async def handler(ctx):
        form = {}  # Keep form data for fields other than files
        files = 0
        async for field in ctx.request.iter_multipart():
            if field.length > 2 * 1024 * 1024:
                return ctx.response.send_error(413, 'Cannot accept files over 2 MB.')

            if field.filename:
                await field.save_file(directory='/var/www/uploads')
                files += 1
            else:
                form[field.name] = await field.read()

        return 'Thank you, {firstname} {lastname}! {files} successfully uploaded.'.\
            format(files=files, **form)

Stream a response::

    # Python 3.6 and above
    async def handler(ctx):
        # Send just a number in each chunk at 1 second intervals
        for i in range(5, 0, -1):
            yield '%d\n' % i
            await asyncio.sleep(1)

        # Send JSON data in the last chunk
        return ctx.serialize({'numbers sent': 5, 'message': 'This is the last chunk'})

    # Python 3.5
    async def handler(ctx):
        from asyncio_extras import yield_async

        # Send just a number in each chunk at 1 second intervals
        for i in range(5, 0, -1):
            await yield_async('%d\n' % i)
            await asyncio.sleep(1)

        # Send JSON data in the last chunk
        return ctx.serialize({'numbers sent': 5, 'message': 'This is the last chunk'})

