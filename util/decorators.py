from functools import wraps
from asyncio import CancelledError

def cancelable(func):

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except CancelledError:
            pass

        return None

    return wrapper
