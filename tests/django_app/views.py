from asphalt.core import Dependency, inject
from django.http import HttpRequest, HttpResponse, JsonResponse


@inject
async def index(
    request: HttpRequest,
    my_resource: str = Dependency(),
    another_resource: str = Dependency("another"),
) -> HttpResponse:
    return JsonResponse(
        {
            "message": request.GET["param"],
            "my resource": my_resource,
            "another resource": another_resource,
        }
    )
