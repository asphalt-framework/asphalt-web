from pathlib import Path, PurePath
from typing import Union, Optional, cast

from asphalt.core.context import Context
from asphalt.web.api import AbstractEndpoint, Router
from typeguard import check_argument_types

from asphalt.web.request import HTTPRequest


class StaticFileEndpoint(AbstractEndpoint):
    __slots__ = 'path'

    def __init__(self, path: Path):
        self.path = path

    def begin_request(self, parent_ctx: Context, request: HTTPRequest):
        if request.method != 'GET':
            raise HTTPMethodNotAllowed(request.method, ['GET'])


class StaticFileRouter(Router):
    __slots__ = 'basedir'

    def __init__(self, basedir: Union[str, Path]):
        assert check_argument_types()
        self.basedir = Path(basedir)

    def resolve(self, request: HTTPRequest, path: PurePath) -> Optional[AbstractEndpoint]:
        final_path = cast(Path, self.basedir / path)
        return StaticFileEndpoint(final_path) if final_path.is_file() else None

