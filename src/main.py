import asyncio
import logging
import uvloop
from src.containers import AppContainer


async def main():
    loop = asyncio.get_running_loop()
    container = AppContainer()
    await container.init_resources()
    logging.info("Starting AppContainer")
    listener = await container.listener()
    await listener.authenticate()

    # TODO: Вспомнить, зачем нужна многопоточка
    await listener.listen()


if __name__ == "__main__":
    uvloop.install()
    asyncio.run(main())
