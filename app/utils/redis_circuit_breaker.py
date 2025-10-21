from app.utils.redis_client import redis_client

# --- Configurable constants (you can later move to settings.py) ---
FAIL_MAX = 5
RESET_TIMEOUT = 30  # seconds


def circuit_keys(name: str):

    return {
        "state": f"cb:{name}:state",
        "failures": f"cb:{name}:failures",
    }


async def get_state(name: str) -> str:
    keys = circuit_keys(name)
    state = await redis_client.get(keys["state"])
    return state or "closed"


async def set_state(name: str, state: str):
    keys = circuit_keys(name)
    await redis_client.set(keys["state"], state, ex=RESET_TIMEOUT)
    if state == "open":
        print(f"[ALERT] Circuit '{name}' OPEN — blocking for {RESET_TIMEOUT}s")


async def increment_failures(name: str) -> int:

    keys = circuit_keys(name)
    failures = await redis_client.incr(keys["failures"])
    await redis_client.expire(keys["failures"], RESET_TIMEOUT)
    return int(failures)


async def reset_failures(name: str):

    keys = circuit_keys(name)
    await redis_client.delete(keys["failures"])


async def execute_with_breaker(name: str, func, *args, fail_max: int = FAIL_MAX, reset_timeout: int = RESET_TIMEOUT, **kwargs):

    state = await get_state(name)
    if state == "open":
        raise Exception(f"Circuit '{name}' is open — skipping external call")

    try:
        result = await func(*args, **kwargs)
        await reset_failures(name)
        return result

    except Exception as e:
        failures = await increment_failures(name)
        if failures >= fail_max:
            await set_state(name, "open")
        raise e
