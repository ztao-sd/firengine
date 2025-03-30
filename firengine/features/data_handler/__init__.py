from abc import ABC, abstractmethod


class AbstractBaseDataHandler[T](ABC):
    @abstractmethod
    def handle(data: T):
        pass


class PrintDataHandler[T](AbstractBaseDataHandler[T]):
    def handle(self, data: T):
        print(data)
