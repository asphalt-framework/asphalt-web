import logging
from typing import List, Tuple, Union, Dict, Any

from asphalt.core import ContainerComponent, Context, merge_config, PluginContainer
from typeguard import check_argument_types

from asphalt.web.servers.base import BaseWebServer

logger = logging.getLogger(__name__)
servers = PluginContainer('asphalt.web.servers', BaseWebServer)


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
            config.setdefault('context_attr', resource_name)
            context_attr, server = self.configure_server(**config)
            self.servers.append((resource_name, context_attr, server))

    @classmethod
    def configure_server(cls, context_attr: str, server: Union[BaseWebServer, str] = 'http',
                         **server_options) -> Tuple[str, BaseWebServer]:
        """
        Configure a web server.

        :param context_attr: context attribute of the server (if omitted, the resource name
            will be used instead)
        :param server: server instance or a plugin name in the ``asphalt.web.servers`` namespace
        :param server_options: keyword arguments passed to the constructor of the server class if
            ``server`` is a plugin name

        """
        assert check_argument_types()
        if isinstance(server, str):
            return context_attr, servers.create_object(BaseWebServer, **server_options)
        else:
            return context_attr, server

    async def start(self, ctx: Context):
        for resource_name, context_attr, server in self.servers:
            await server.start(ctx)
            ctx.publish_resource(BaseWebServer, resource_name, context_attr)
