import logging
from io import BytesIO
from pathlib import Path

from PIL import Image
from selenium.webdriver import Chrome
from selenium.common import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from src.models import TaskStatus, TaskModel
from src.parser.xpaths import (
    error_button_xpath,
    on_profile_second_xpath,
    business_photo_xpath,
    photo_xpath,
)


class WhatsappParser:
    url: str
    webdriver: Chrome
    wait_timeout: int
    logger: logging.Logger
    photos_dir: Path

    def __init__(
        self,
        driver: Chrome,
        logger: logging.Logger = logging.getLogger("Parser"),
    ):
        self.url = "https://web.whatsapp.com/send?phone={0}"
        self.logger = logger
        self.webdriver_timeout = 10
        self.webdriver = driver

    async def save_photo(self, element: WebElement, number: TaskModel):
        image = Image.open(BytesIO(element.screenshot_as_png))

        # image = Image.open(self.photos_dir / (number.number + ".png"))
        image_bytes = BytesIO()
        image.resize((image.size[0] // 2, image.size[1] // 2), Image.ANTIALIAS).save(
            image_bytes, "PNG", optimise=True, quality=50
        )

        number.image = image_bytes.getvalue()
        self.logger.info(f"Фотография {number.number}.png сохранена")

    async def parse(self, task: TaskModel) -> None:
        try:
            self.webdriver.get(self.url.format(task.number))
            try:
                WebDriverWait(self.webdriver, self.wait_timeout).until(
                    EC.element_to_be_clickable((By.XPATH, error_button_xpath))
                )
                task.status = TaskStatus.ERROR
            except TimeoutException:
                profile_button = WebDriverWait(self.webdriver, self.wait_timeout).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "_2YnE3"))
                )
                profile_button.click()

                try:
                    second_profile_button = self.webdriver.find_element(
                        By.XPATH, on_profile_second_xpath
                    )
                    second_profile_button.click()
                except NoSuchElementException:
                    second_profile_button = self.webdriver.find_element(
                        By.XPATH, business_photo_xpath
                    )
                    second_profile_button.click()

                photo = WebDriverWait(self.webdriver, self.wait_timeout).until(
                    EC.element_to_be_clickable((By.XPATH, photo_xpath))
                )
                await self.save_photo(photo, task)
                task.status = TaskStatus.COMPLETED

        except Exception as e:
            self.logger.error(f"Parsing error: {e}")
            if task.status == TaskStatus.SECONDCHECK:
                task.status = TaskStatus.ERROR
            else:
                task.status = TaskStatus.SECONDCHECK
