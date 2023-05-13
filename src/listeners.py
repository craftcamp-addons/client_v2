from logging import Logger, getLogger
from typing import Any

from nats import NATS
from nats.aio.msg import Msg
from nats.errors import NoRespondersError

from src import utils
from src.models import InitMessageModel, TaskMessageModel
from src.parser.exceptions import ParserException
from src.parser.parser import Parser


class NatsListener:
    worker_id: int
    nats: NATS
    logger: Logger
    parser_factory: Any

    def __init__(self, connection: NATS, worker_id: int, parser_factory):
        self.nats = connection
        self.worker_id = worker_id
        self.logger = getLogger(self.__class__.__name__)
        self.parser_factory = parser_factory

    async def authenticate(self):
        try:
            self.logger.info("Authentication request sent")
            init_res: Msg | None = await self.nats.request(
                "init",
                utils.pack_msg(InitMessageModel(worker_id=self.worker_id)),
                timeout=10,
            )

            init_response: InitMessageModel = utils.unpack_msg(
                init_res, InitMessageModel
            )
            if init_response.worker_id != self.worker_id:
                raise RuntimeError(
                    f"Authentication error: {self.worker_id=} {init_response.worker_id=}"
                )

            self.logger.info(f"Authentication successful {self.worker_id=}")
        except Exception as e:
            self.logger.exception(e)

    async def listen(self):
        js = self.nats.jetstream()
        await js.add_stream(
            name="tasks", subjects=["server.numbers.*", "worker.task.numbers"]
        )

        subscriber = await js.pull_subscribe(
            subject=f"worker.task.numbers", durable=f"worker_numbers"
        )

        while True:
            parser = self.parser_factory()
            for message in await subscriber.fetch(batch=5):
                try:
                    task = utils.unpack_msg(message, TaskMessageModel)
                    await parser.parse(task.model, self.worker_id)
                    await message.ack()
                except Exception as e:
                    self.logger.error(e)
                    return
