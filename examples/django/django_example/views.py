from django.http import HttpRequest, HttpResponse


async def index(request: HttpRequest) -> HttpResponse:
    return HttpResponse(b"Hello, world!")
