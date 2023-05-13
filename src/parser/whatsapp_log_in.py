import base64
import logging
from typing import Generator

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from src.parser.xpaths import user_header_xpath, qr_code_xpath


class WhatsappLogIn:
    driver: webdriver.Chrome

    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver

    def log_in(self, timeout: int) -> Generator[None, None, bytes | bool]:
        try:
            self.driver.get("https://web.whatsapp.com")
            yield base64.b64decode(
                self.driver.execute_script(
                    "return arguments[0].toDataURL('image/png').substring(21);",
                    WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_element_located((By.XPATH, qr_code_xpath))
                    ),
                )
            )
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, user_header_xpath))
            )
            yield True
        except TimeoutException:
            yield False
        except Exception as e:
            raise e
