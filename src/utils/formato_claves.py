"""Normaliza claves de municipio y localidad al formato oficial de ancho fijo."""


def formatear_clave_municipio(clave) -> str:
    """Normaliza cualquier clave de municipio a 3 dígitos con ceros a la izquierda."""
    return f"{int(clave):03d}"


def formatear_clave_localidad(clave) -> str:
    """Normaliza cualquier clave de municipio a 4 dígitos con ceros a la izquierda."""
    return f"{int(clave):04d}"
