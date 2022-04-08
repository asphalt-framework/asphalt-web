from asphalt.core import Dependency, inject
from django.http import HttpRequest, HttpResponse, JsonResponse

from .component import MyResource


@inject
async def index(
    request: HttpRequest,
    my_resource: MyResource = Dependency(),
    another_resource: MyResource = Dependency("another"),
) -> HttpResponse:
    return JsonResponse(
        {
            "message": "Hello World",
            "my resource": my_resource.description,
            "another resource": another_resource.description,
        }
    )
