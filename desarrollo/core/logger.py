"""
==============================================================
SIMI

logger.py

Configuración base de logs.
==============================================================
"""

import logging
from pathlib import Path


LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "simi.log"


def configurar_logger():
    LOG_DIR.mkdir(exist_ok=True)

    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )


def registrar_info(mensaje: str):
    configurar_logger()
    logging.info(mensaje)


def registrar_error(mensaje: str):
    configurar_logger()
    logging.error(mensaje)