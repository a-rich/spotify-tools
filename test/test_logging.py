import logging
import sys

from spotify_tools.logging import get_logger


def test_get_logger_basic_properties():
    logger_name = "my_test_logger"
    logger = get_logger(logger_name)

    # Logger name matches
    assert logger.name == logger_name

    # Logger level is INFO
    assert logger.level == logging.INFO

    # Logger propagation is disabled
    assert logger.propagate is False

    # Logger has exactly one handler
    handlers = logger.handlers
    assert len(handlers) == 1

    handler = handlers[0]

    # Handler is a StreamHandler
    assert isinstance(handler, logging.StreamHandler)

    # Handler outputs to sys.stdout
    assert handler.stream is sys.stdout

    # Handler formatter format string
    formatter = handler.formatter
    assert (
        formatter._fmt
        == "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    assert formatter.datefmt == "%Y-%m-%d %H:%M:%S"


def test_get_logger_does_not_add_multiple_handlers():
    logger_name = "my_test_logger_multi"

    # Get logger twice, second call should NOT add extra handlers
    logger1 = get_logger(logger_name)
    logger2 = get_logger(logger_name)

    assert len(logger1.handlers) == 1
    assert logger1.handlers == logger2.handlers  # same handlers list


def test_logger_logs_at_info_level(caplog):
    logger = get_logger("test_info_log")

    # Temporarily enable propagation so caplog can see logs
    old_propagate = logger.propagate
    logger.propagate = True

    with caplog.at_level(logging.INFO):
        logger.info("This is an info message.")
        logger.debug("This debug message should NOT appear.")

    logger.propagate = old_propagate

    # Only the info message should be captured
    assert "This is an info message." in caplog.text
    assert "debug message" not in caplog.text.lower()
