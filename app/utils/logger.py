import logging
from pathlib import Path


def setup_logger(name: str, log_level: str = "INFO", log_dir: str = "logs") -> logging.Logger:
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    if not logger.handlers:
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        fh = logging.FileHandler(f"{log_dir}/app.log")
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger
