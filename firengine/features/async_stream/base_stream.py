import traceback
from collections.abc import AsyncIterable

from aioreactive import AsyncSubject


class BaseStream[T](AsyncSubject):
    def __init__(self, async_iter: AsyncIterable[T] | None = None):
        super().__init__()
        self._async_iter = async_iter
        self._streaming = False

    async def async_run(self):
        self._streaming = True
        async_iter = aiter(self._async_iter)
        while self._streaming:
            try:
                obj = await anext(async_iter)
                await self.asend(obj)
            except StopAsyncIteration as err:
                self._streaming = False
                print("stop", err)
                traceback.print_exc()
            except Exception as err:
                print(err)
                traceback.print_exc()
