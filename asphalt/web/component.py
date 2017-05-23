import logging
from typing import List, Tuple, Dict, Any

from asphalt.core import (
    ContainerComponent, Context, merge_config, PluginContainer,
    context_teardown)
from async_generator import yield_
from typeguard import check_argument_types

from asphalt.web.servers.base import BaseWebServer

logger = logging.getLogger(__name__)
server_types = PluginContainer('asphalt.web.servers', BaseWebServer)


class WebServerComponent(ContainerComponent):
    """
    Starts one or more HTTP servers and publishes them as
    :class:`asphalt.web.server.base.BaseWebServer` resources.

    If more than one server is to be configured, provide a ``servers`` argument as a
    list where each element is a dictionary of keyword arguments to :meth:`configure_server`.
    Otherwise, directly pass those keyword arguments to the component constructor itself.

    :param servers: sequence of server configurations (keyword arguments to
        :meth:`configure_server`)
    :param default_server_args: default values for omitted :meth:`configure_server` arguments
    """

    def __init__(self, components: Dict[str, Dict[str, Any]] = None,
                 servers: Dict[str, Dict[str, Any]] = None, **default_server_args):
        super().__init__(components)
        assert check_argument_types()

        if not servers:
            default_server_args.setdefault('context_attr', 'webserver')
            servers = {'default': default_server_args}

        self.servers = []  # type: List[Tuple[str, str, BaseWebServer]]
        for resource_name, config in servers.items():
            config = merge_config(default_server_args, config)
            context_attr = config.pop('context_attr', resource_name)
            server = server_types.create_object(**config)
            self.servers.append((resource_name, context_attr, server))

    @context_teardown
    async def start(self, ctx: Context):
        for resource_name, context_attr, server in self.servers:
            await server.start(ctx)
            ctx.add_resource(server, resource_name, context_attr, BaseWebServer)
            logger.info('Started %s (%s / ctx.%s)', server.__class__.__name__, resource_name,
                        context_attr)

        await yield_()

        for resource_name, context_attr, server in self.servers:
            await server.shutdown()
            logger.info('Shut down %s (%s)', server.__class__.__name__, resource_name)
