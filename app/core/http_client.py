import httpx

async_client = httpx.AsyncClient(
    timeout=httpx.Timeout(5.0),
    limits=httpx.Limits(
        max_keepalive_connections=20,
        max_connections=100
    )
)