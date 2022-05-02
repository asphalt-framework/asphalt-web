from asphalt.core import inject, resource
from django.http import HttpRequest, HttpResponse, JsonResponse


@inject
async def index(
    request: HttpRequest,
    my_resource: str = resource(),
    another_resource: str = resource("another"),
) -> HttpResponse:
    return JsonResponse(
        {
            "message": request.GET["param"],
            "my resource": my_resource,
            "another resource": another_resource,
        }
    )
