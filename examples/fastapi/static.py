from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

application = FastAPI()


@application.get("/", response_class=PlainTextResponse)
async def root() -> str:
    return "Hello, world!"
