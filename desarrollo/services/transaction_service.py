"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

transaction_service.py

Servicio genérico para control de transacciones.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""


class TransactionService:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self.conn

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            self.conn.rollback()
            return False

        self.conn.commit()
        return True