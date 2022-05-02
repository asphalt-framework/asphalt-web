from fastapi import FastAPI, Response

application = FastAPI()


@application.get("/")
async def root() -> Response:
    return Response("Hello, world!")
