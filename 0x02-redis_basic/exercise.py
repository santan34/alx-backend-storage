#!/usr/bin/env python3
"""
Caching with redis
"""

import redis
import uuid
from functools import wraps
from typing import Union, Any, Optional, Callable

def count_calls(method: Callable) -> Callable:
    """ Decorator for Cache class methods to track call count
    """
    @wraps(method)
    def wrapper(self: Any, *args, **kwargs) -> str:
        """ Wraps called method and adds its call count redis before execution
        """
        self._redis.incr(method.__qualname__)
        return method(self, *args, **kwargs)
    return wrapper


def call_history(method: Callable) -> Callable:
    """ Decorator for Cache class method to track args
    """
    @wraps(method)
    def wrapper(self: Any, *args) -> str:
        """ Wraps called method and tracks its passed argument by storing
            them to redis
        """
        self._redis.rpush(f'{method.__qualname__}:inputs', str(args))
        output = method(self, *args)
        self._redis.rpush(f'{method.__qualname__}:outputs', output)
        return output
    return wrapper


def replay(fn: Callable) -> None:
    """ Check redis for how many times a function was called and display:
            - How many times it was called
            - Function args and output for each call
    """
    client = redis.Redis()
    calls = client.get(fn.__qualname__).decode('utf-8')
    inputs = [input.decode('utf-8') for input in
              client.lrange(f'{fn.__qualname__}:inputs', 0, -1)]
    outputs = [output.decode('utf-8') for output in
               client.lrange(f'{fn.__qualname__}:outputs', 0, -1)]
    print(f'{fn.__qualname__} was called {calls} times:')
    for input, output in zip(inputs, outputs):
        print(f'{fn.__qualname__}(*{input}) -> {output}')


class Cache:
    """a cacheing class"""
    def __init__(self) -> None:
        """init of a cache object"""
        self._redis = redis.Redis()
        self._redis.flushdb()

    @call_history
    @count_calls
    def store(self, data: Union[str, float, bytes, int]) -> str:
        """stores data stored in redis using a random uuid"""
        key = str(uuid.uuid4())
        self._redis.set(key, data)
        return key
    
    def get(self, key: str, fn: Optional[Callable] = None) -> Any:
        """
        gets a value in correct datatype
        """
        client = self._redis
        value = client.get(key)
        if not value:
            return
        if fn:
            return fn(value)
        return value
    
    def get_str(self, data: str) -> str:
        "decodes to string"
        return str(data)
    
    def get_int(self, data: str) -> int:
        """decodes to string"""
        return int(data)