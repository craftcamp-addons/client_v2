import sys

import nats
from dependency_injector import containers, providers
import logging
from src.config import Settings
from src.listeners import NatsListener
from src.parser.parser import Parser


class AppContainer(containers.DeclarativeContainer):
    config = providers.Configuration(pydantic_settings=[Settings()])

    nats_connection = providers.Resource(nats.connect, config.mq_settings.dsn)

    logging = providers.Resource(
        logging.basicConfig,
        format=config.logging.format,
        level=config.logging.level,
        stream=sys.stdout,
    )

    parser_factory = providers.Factory(
        Parser, nats=nats_connection, worker_id=config.worker_id
    )

    listener = providers.ThreadSafeSingleton(
        NatsListener, nats_connection, config.worker_id, parser_factory
    )


