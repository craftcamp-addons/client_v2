import logging
from pathlib import Path
from typing import Protocol, Generator

import xvfbwrapper
from nats import NATS
from nats.js import JetStreamContext
from selenium import webdriver
from selenium.common import WebDriverException
from xvfbwrapper import Xvfb

from src import utils
from src.models import TaskModel, LoginMessageModel
from src.parser.exceptions import ParserException
from src.parser.whatsapp_log_in import WhatsappLogIn
from src.parser.whatsapp_parser import WhatsappParser


class ParserImpl(Protocol):
    async def parse(self, number: TaskModel) -> None:
        pass


class LogIn(Protocol):
    def log_in(self, timeout: int) -> Generator[None, None, bytes | bool]:
        pass


class Parser:
    js: JetStreamContext
    display: Xvfb
    parser: ParserImpl
    user_logger: LogIn
    driver: webdriver.Chrome | None = None

    logger: logging.Logger = logging.getLogger("Parser")

    def __init__(self, nc: NATS):
        self.js = nc.jetstream()

    async def parse(self, task: TaskModel, worker_id: int):
        if self.driver is None:
            self.display = xvfbwrapper.Xvfb()
            self.display.start()
            try:
                options = webdriver.ChromeOptions()
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--allow-profiles-outside-user-dir")
                options.add_experimental_option("detach", True)
                options.add_experimental_option("excludeSwitches", ["enable-logging"])
                options.add_argument("--enable-profile-shortcut-manager")
                options.add_argument(
                    f'--user-data-dir={Path("/chromedriver_data") / "user"}'
                )
                options.add_argument("--profile-directory=Profile 1")

                self.driver = webdriver.Chrome(
                    executable_path=(Path("/chromedriver")),
                    options=options,
                )
            except WebDriverException as e:
                raise ParserException(f"Не удалось запустить chromedriver: {e.__str__()[:30]}")
            self.parser = WhatsappParser(self.driver)
            self.user_logger = WhatsappLogIn(self.driver)

        try:
            for res in self.user_logger.log_in(60):
                match res:
                    case True:
                        self.logger.info("Успешный вход")
                        break
                    case False:
                        self.logger.error("Не удалось войти")
                        continue
                    case screenshot:
                        await self.js.publish(
                            "server.login",
                            payload=utils.pack_msg(
                                LoginMessageModel(
                                    worker_id=worker_id, login_screenshot=screenshot
                                )
                            ),
                        )

            self.logger.info(f"Parsing: {task.dict()}")
            await self.parser.parse(task)

            await self.js.publish("server.results",
                                  payload=utils.pack_msg(task))

        except Exception as e:
            self.driver.quit()
            self.driver = None
            self.display.stop()

            raise ParserException(e)
