import logging
from lzma import decompress, compress
from typing import Type, TypeVar

import ormsgpack
from nats.aio.msg import Msg
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def unpack_msg(msg: Msg, message_type: Type[T]) -> T:
    return message_type.parse_obj(ormsgpack.unpackb(decompress(msg.data)))


def pack_msg(msg: T) -> bytes:
    return compress(ormsgpack.packb(msg.dict()))
