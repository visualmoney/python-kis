import logging

import pytest
from colorlog import ColoredFormatter

from pykis import logging as pykis_logging


def test_create_logger():
    """_create_logger 함수가 로거를 올바르게 생성하는지 테스트합니다."""
    logger_name = "test_logger"
    logger_level = logging.DEBUG

    logger = pykis_logging._create_logger(logger_name, logger_level)

    assert isinstance(logger, logging.Logger)
    assert logger.name == logger_name
    assert logger.level == logger_level
    assert len(logger.handlers) == 1

    handler = logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    assert isinstance(handler.formatter, ColoredFormatter)


def test_global_logger_instance():
    """전역 로거 인스턴스가 올바르게 생성되었는지 테스트합니다."""
    assert isinstance(pykis_logging.logger, logging.Logger)
    assert pykis_logging.logger.name == "pykis"
    assert pykis_logging.logger.level == logging.INFO


@pytest.mark.parametrize(
    "level_input, expected_level",
    [
        ("DEBUG", logging.DEBUG),
        ("INFO", logging.INFO),
        ("WARNING", logging.WARNING),
        ("ERROR", logging.ERROR),
        ("CRITICAL", logging.CRITICAL),
        (logging.DEBUG, logging.DEBUG),
        (logging.INFO, logging.INFO),
        (logging.WARNING, logging.WARNING),
        (logging.ERROR, logging.ERROR),
        (logging.CRITICAL, logging.CRITICAL),
    ],
)
def test_set_level(level_input, expected_level):
    """setLevel 함수가 로거 레벨을 올바르게 설정하는지 테스트합니다."""
    initial_level = pykis_logging.logger.level

    try:
        pykis_logging.setLevel(level_input)
        assert pykis_logging.logger.level == expected_level
    finally:
        # 테스트 후 원래 레벨로 복원
        pykis_logging.logger.setLevel(initial_level)

