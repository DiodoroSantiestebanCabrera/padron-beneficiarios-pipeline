"""Genera un dataset sintético del padrón, reproduciendo las anomalías
reales documentadas en reglas_negocio_calidad_padron_bienestar.md."""

import random
from datetime import date

import pandas as pd
from faker import Faker

from src.utils.catalogos import cargar_catalogos

fake = Faker("es_MX")
random.seed(42)  # reproducible: los mismos datos "aleatorios" cada vez que se corre


LAT_CONSTANTE = 19.305824
LON_CONSTANTE = -98.240997

GENERO_A_SEXO_CURP = {"Masculino": "H", "Femenino": "M"}
# Valores tal como se observan capturados en el OLTP real -- sin normalizar
# a propósito (mayúsculas/minúsculas/paréntesis inconsistentes). La limpieza
# de esto es responsabilidad de silver/limpieza.py, no de este generador.

NIVELES_ESCOLARIDAD = [
    "Carrera Tecnica",
    "Licenciatura",
    "No capturado",
    "Otra",
    "Posgrado",
    "Preescolar",
    "Preparatoria",
    "Primaria",
    "Secundaria",
    "Sin Escolaridad",
]
ESTADOS_CIVILES = [
    "Casado",
    "CONCUBINATO",
    "Divorciado (a)",
    "OTRO",
    "SEPARADO(A)",
    "Soltero",
    "Union libre",
    "viudo (a)",
]

# Confirmado en datos reales: el 100% de los registros trae "Titular" --
# no es una lista de opciones, es un valor fijo.
PARENTESCO_UNICO_OBSERVADO = "Titular"

# Estimado, sin tasa real medida todavía -- ajustar si hay más evidencia.
PROBABILIDAD_EDAD_NO_CAPTURADA = 0.05


def _fecha_referencia(anio_mes: str) -> date:
    """Convierte 'YYYY-MM' en una fecha (el día 1 de ese mes)."""
    # Split toma el texto y lo corta (separa) cada que encuentra el guion(algo visual asi: 2023-05 resultado ["2023","05"])
    # Recorre esa lista y convierte cada pedazo de texto en un número entero
    anio, mes = (int(parte) for parte in anio_mes.split("-"))
    return date(anio, mes, 1)


def _generar_fecha_nacimiento(edad: int, fecha_referencia: date) -> date:
    """Calcula una fecha de nacimiento consistente con una edad dada."""
    anio_nacimiento = fecha_referencia.year - edad
    mes_nacimiento = random.randint(1, 12)
    dia_nacimiento = random.randint(1, 28)

    return date(anio_nacimiento, mes_nacimiento, dia_nacimiento)


def _corromper_encoding(texto: str, probabilidad: float) -> str:
    """Simula el mojibake real (acentos rotos con '?') a una tasa dada."""
    # De la caja de herramientas llamada random, saca la herramienta específica llamada random()
    if random.random() < probabilidad:
        for original, roto in [("á", "?"), ("é", "?"), ("í", "?"), ("ó", "?")]:
            # replace() primer argumento busca(valor original) y lo reemplaza por lo roto(el simbolo ?)
            texto = texto.replace(original, roto)
    return texto


def _generar_curp_valida(fecha_nacimiento: date, sexo_curp: str) -> str:
    """Arma un CURP de 18 caracteres usando la fecha de nacimiento y el
    sexo REALES de esta fila -- independiente de si la columna EDAD
    termina capturada o no en la fila final."""
    letras = fake.random_uppercase_letter
    consonantes = "BCDFGHJKLMNPQRSTVWXYZ"
    partes = [
        # Ejecuta la función letras() 4 veces(range 4), obteniendo una letra en cada ejecución
        "".join(letras() for _ in range(4)),
        fecha_nacimiento.strftime("%y%m%d"),
        sexo_curp,
        "TL",
        # {random.randint(0, 99)(1, 12):(1, 28):02d}..." ->genera fecha nacimiento (dd/mm/yyyy) pero que solo tenga 2 digitos(:02d rellena con ceros a la izq)
        # random.choice elige aleaoriamente el sexo "H" o "M"
        "".join(random.choice(consonantes) for _ in range(3)),
        random.choice("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        str(random.randint(0, 9)),
    ]
    return "".join(partes)


def generar_padron_sintetico(
    n_filas: int = 195_000, anio_mes: str = "2026-07"
) -> pd.DataFrame:
    """Genera un padrón sintético con las 29 columnas reales del reporte
    mensual del OLTP, reproduciendo las anomalías de calidad ya documentadas."""

    catalogos = cargar_catalogos()
    fecha_referencia = _fecha_referencia(anio_mes)
    filas = []

    for i in range(n_filas):
        # --- Identidad: la edad se calcula siempre, para un CURP coherente,
        # sin importar si más abajo la columna EDAD termina vacía o no ---
        genero = random.choice(list(GENERO_A_SEXO_CURP.keys()))
        edad_real = random.randint(0, 99)
        fecha_nacimiento = _generar_fecha_nacimiento(edad_real, fecha_referencia)
        curp = _generar_curp_valida(fecha_nacimiento, GENERO_A_SEXO_CURP[genero])

        # --- Geografía ---
        clave_municipio_oficial, municipio_oficial = random.choice(catalogos.municipios)
        municipio = municipio_oficial
        if municipio == "Tlaxcala" and random.random() < 0.001:
            municipio = "TLAXCALA"
        municipio = _corromper_encoding(municipio, probabilidad=0.10)

        opciones_colonia = catalogos.localidades_por_municipio.get(
            clave_municipio_oficial, ["Centro"]
        )
        colonia = _corromper_encoding(
            random.choice(opciones_colonia), probabilidad=0.03
        )

        lat, lon = LAT_CONSTANTE, LON_CONSTANTE
        if random.random() < 0.002:
            lon = lat

        # --- Folio ---
        folio = 225_001 + i
        if random.random() < 0.002:
            folio = random.randint(100_000, 110_000)

        fila = {
            "FECHA DE REGISTRO": date(
                fecha_referencia.year, fecha_referencia.month, random.randint(1, 28)
            ),
            "FOLIO DE TARJETA": folio,
            "RFC": fake.bothify("????######???"),
            "CURP": curp,
            "NOMBRE": fake.first_name(),
            "APELLIDO PATERNO": fake.last_name(),
            "APELLIDO MATERNO": fake.last_name(),
            "EDAD": edad_real
            if random.random() > PROBABILIDAD_EDAD_NO_CAPTURADA
            else None,
            "F. NAC.": fecha_nacimiento,
            "CELULAR": fake.numerify("246########"),
            "TEL.CASA": fake.numerify("246########")
            if random.random() > 0.998
            else None,
            "ESCOLARIDAD": random.choice(NIVELES_ESCOLARIDAD),
            "GRADO": str(random.randint(1, 6)) if random.random() > 0.08 else None,
            "GENERO": genero,
            "EDO. CIVIL": random.choice(ESTADOS_CIVILES),
            "CALLE": fake.street_name(),
            "No.EXT": str(random.randint(1, 999)),
            "No.INT": str(random.randint(1, 20)) if random.random() > 0.88 else None,
            "CLAVE LOCALIDAD": random.randint(1, 60)
            if random.random() > 0.013
            else None,
            "COLONIA": colonia if random.random() > 0.002 else None,
            "CLAVE MUNICIPIO": random.randint(1, 60)
            if random.random() > 0.01
            else None,
            "MUNICIPIO": municipio if random.random() > 0.003 else None,
            "EDO.": "Tlaxcala" if random.random() > 0.003 else None,
            "CODIGO POSTAL": f"{random.randint(90000, 90999)}",
            "LATITUD": lat,
            "LONGITUD": lon,
            "PARENTESCO": PARENTESCO_UNICO_OBSERVADO,
            "SUCURSAL": f"Módulo {municipio_oficial}",
            "SECCION ELECTORAL": random.randint(1, 200)
            if random.random() > 0.27
            else None,
        }
        filas.append(fila)

    return pd.DataFrame(filas)


if __name__ == "__main__":
    df = generar_padron_sintetico()
    ruta_salida = "data/synthetic/padron_sintetico_2026-07.csv"
    df.to_csv(ruta_salida, index=False, encoding="utf-8")
    print(f"Generadas {len(df)} filas sintéticas en {ruta_salida}")


def generar_periodo_siguiente(
    padron_previo: pd.DataFrame,
    n_filas_nuevas: int = 1_580,
    anio_mes: str = "2026-08",
    proporcion_curps_repetidas: float = 0.1,
) -> pd.DataFrame:
    """Genera un lote nuevo simulando el mes siguiente: una parte de las
    CURPs coincide a propósito con personas ya presentes en `padron_previo`
    (actualización real, con folio nuevo), y el resto son personas nuevas."""
    padron_nuevo = generar_padron_sintetico(n_filas=n_filas_nuevas, anio_mes=anio_mes)

    folio_inicial = int(padron_previo["FOLIO DE TARJETA"].max()) + 1
    padron_nuevo["FOLIO DE TARJETA"] = range(
        folio_inicial, folio_inicial + n_filas_nuevas
    )

    n_actualizaciones = int(n_filas_nuevas * proporcion_curps_repetidas)
    curps_a_reemplazar = (
        padron_previo["CURP"].sample(n=n_actualizaciones, random_state=1).tolist()
    )
    padron_nuevo.loc[: n_actualizaciones - 1, "CURP"] = curps_a_reemplazar

    return padron_nuevo
