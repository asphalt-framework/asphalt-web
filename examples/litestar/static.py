from litestar import get


@get("/")
async def root() -> str:
    return "Hello, world!"
