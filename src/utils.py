import json
import logging
import os
import time

from src.settings import config

from datetime import datetime, timedelta
from pathlib import Path
from sys import stdout
from urllib.parse import urljoin
from pyspark.sql import SparkSession

import requests


def get_datetime_now():
    return datetime.now().strftime("%Y-%m-%d-%H-%M")


LOG_FILE_PATH = os.path.join(Path(__file__).parent.parent.absolute(), 'logs', f"eve_online_{get_datetime_now()}.log")


def get_date_today():
    return datetime.today().strftime('%Y-%m-%d')


def get_date_yesterday():
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")


def get_logger(logger_name):
    print("Logs will be saved to: ", LOG_FILE_PATH)
    os.makedirs(os.path.join(Path(__file__).parent.absolute(), 'logs'), exist_ok=True)
    logger = logging.getLogger(logger_name)
    if logger.hasHandlers():  # Prevent duplicate handlers
        return logger

    logger.setLevel(logging.DEBUG)
    log_file_formatter = logging.Formatter(
        fmt=f"%(levelname)s \t %(message)s \t %(asctime)s (%(relativeCreated)d) - %(filename)s:%(funcName)s():%(lineno)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = logging.FileHandler(filename=LOG_FILE_PATH)
    file_handler.setFormatter(log_file_formatter)
    file_handler.setLevel(level=logging.DEBUG)
    logger.addHandler(file_handler)

    log_stream_formatter = logging.Formatter(
        fmt=f"%(levelname)-8s %(message)s \t \t %(asctime)s - %(filename)s:%(funcName)s:%(lineno)s",
        datefmt="%H:%M:%S"
    )
    console_handler = logging.StreamHandler(stream=stdout)
    console_handler.setFormatter(log_stream_formatter)
    console_handler.setLevel(level=logging.INFO)

    logger.addHandler(console_handler)

    return logger


def get_date_range():
    date_to = datetime.now()
    date_from = (date_to - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    date_from_str = date_from.strftime('%Y-%m-%d')
    date_to_str = date_to.strftime('%Y-%m-%d')
    return date_from_str, date_to_str


def get_url(url_name):
    return urljoin(config.BASE_URL, url=f"{config.API_VERSION}{url_name}")


def fetch_data_from_api(url, region_id: int = None, type_id: int = None) -> dict:
    logger = get_logger("API requests")
    url = get_url(url_name=url)
    logger.debug("Fetching data from URL: %s", url)
    try:
        resp = requests.get(url, verify=True)
        resp.raise_for_status()
        response_headers = resp.headers
        err_limit = int(resp.headers.get('X-Esi-Error-Limit-Remain', 100))
        err_limit_reset = int(resp.headers.get('X-Esi-Error-Limit-Reset', 60))
        logger.debug("API response headers: %s", resp.headers)
        if err_limit < 100:
            logger.warning("ATTENTION: You have %s errors left to reach the limit", err_limit)
        if err_limit < 5:
            logger.warning("Error limit (almost) reached. Waiting for reset for %s seconds.. ", err_limit_reset)
            time.sleep(err_limit_reset)
        return resp.json()
    except requests.exceptions.RequestException as err:
        raise ConnectionError(
            ">> Having trouble fetching data >>>\n\n%s" % err
        )


def get_a_spark_session():
    return SparkSession.builder.appName("bdr").getOrCreate()


def save_data(file_path: str, data: dict):
    logger = get_logger("API requests")
    logger.info("Attempting to save the fetched data in file: %s", file_path)
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as oFile:
            oFile.write(json.dumps(data))
    except IOError:
        logger.error("Could not save data to file %s", file_path)
    logger.info("Data successfully saved.")
    return file_path


def get_data_path(file_name: str):
    return os.path.join(Path(__file__).parent.parent.absolute(), 'data', file_name)
