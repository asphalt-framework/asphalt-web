from asphalt.core import _Dependency, inject
from django.http import HttpRequest, HttpResponse, JsonResponse


@inject
async def index(
    request: HttpRequest,
    my_resource: str = _Dependency(),
    another_resource: str = _Dependency("another"),
) -> HttpResponse:
    return JsonResponse(
        {
            "message": request.GET["param"],
            "my resource": my_resource,
            "another resource": another_resource,
        }
    )
