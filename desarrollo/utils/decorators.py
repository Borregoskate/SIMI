"""
Decoradores reutilizables.
"""


def requiere_permiso(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper