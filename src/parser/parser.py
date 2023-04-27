import asyncio
import logging
from pathlib import Path
from typing import Protocol

import xvfbwrapper
from selenium import webdriver
from selenium.common import WebDriverException
from xvfbwrapper import Xvfb

from src.models import TaskModel
from src.parser.exceptions import ParserException
from src.parser.whatsapp_log_in import WhatsappLogIn
from src.parser.whatsapp_parser import WhatsappParser


class ParserImpl(Protocol):
    async def parse(self, number: TaskModel) -> TaskModel:
        pass


class LogIn(Protocol):
    def log_in(self, timeout: int) -> bool:
        pass


class Parser:
    display: Xvfb
    parser: ParserImpl
    user_logger: LogIn
    driver: webdriver.Chrome | None = None

    logger: logging.Logger = logging.getLogger("Parser")

    async def parse(self, task: TaskModel):
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
                self.logger.error(e)
                raise RuntimeError("Не удалось запустить chromedriver")
            self.parser = WhatsappParser(self.driver)
            self.user_logger = WhatsappLogIn(self.driver)

        try:
            while not self.user_logger.log_in(60):
                self.logger.info("User is not logged in. Sending login")

            self.logger.info(f"Parsing: {task.dict()}")
            await self.parser.parse(task)
        except Exception as e:
            self.logger.error(e)
            self.driver.quit()
            self.driver = None
            self.display.stop()

            raise ParserException()
