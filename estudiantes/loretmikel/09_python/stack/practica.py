"""Total vendido por tienda, a partir de ventas.csv, con el stack de la clase.

La misma pregunta que ventas_ia.py: total vendido por tienda, sin cantidades
inválidas, de mayor a menor. Lo que cambia es el cómo:

- Pydantic v2 valida cada fila una sola vez, en la frontera (el CSV).
- Adentro ya no se revisa nada: Polars recibe la tabla validada, con su
  esquema, y hace la suma como una expresión sobre columnas, fuera del
  intérprete.

Corre: python practica.py
"""

import csv
from collections.abc import Iterable
from datetime import date
from pathlib import Path

import polars as pl
from pydantic import BaseModel, ConfigDict, Field, ValidationError

RUTA = Path(__file__).parent / "ventas.csv"

# El esquema de la tabla, decidido una vez: sin él, una lista vacía de ventas
# daría un DataFrame sin columnas y group_by("tienda") no encontraría la columna.
ESQUEMA: dict[str, type[pl.DataType]] = {
    "fecha": pl.Date,
    "tienda": pl.String,
    "producto": pl.String,
    "cantidad": pl.Int64,
    "precio": pl.Float64,
}


# 1. El contrato: la clase Venta, en la sintaxis de Pydantic v2.
class Venta(BaseModel):
    """Una fila de ventas.csv. Pydantic convierte "12.50" → 12.5 o dice por qué no."""

    # Antes: `class Config: anystr_strip_whitespace = True` (v1).
    model_config = ConfigDict(str_strip_whitespace=True)

    fecha: date
    tienda: str
    producto: str
    # Antes: `Optional[int]` más un validador escrito en Python (v1). La regla va
    # en el contrato: gt = greater than, estrictamente mayor que 0, revisada en Rust.
    cantidad: int = Field(gt=0)
    precio: float = Field(gt=0)


def lee_filas(ruta: Path) -> list[dict[str, str]]:
    """Lee el CSV tal cual llega: todo es texto, nada está validado todavía."""
    with ruta.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


# 2. La frontera: qué filas entran y cuáles se descartan lo decide el contrato.
def valida(filas: Iterable[dict[str, str]]) -> list[Venta]:
    """Valida cada fila una vez; la que no cumple el contrato se queda fuera."""
    buenas: list[Venta] = []
    for fila in filas:
        try:
            buenas.append(Venta.model_validate(fila))
        except ValidationError:
            pass
    return buenas


# 3. La suma por tienda con Polars: una expresión sobre columnas, sin for ni apply.
def total_por_tienda(ventas: Iterable[Venta]) -> pl.DataFrame:
    """Total vendido por tienda, de mayor a menor. Las ventas ya vienen validadas."""
    df = pl.DataFrame(list(ventas), schema=ESQUEMA)
    return (
        df.group_by("tienda")
        .agg((pl.col("cantidad") * pl.col("precio")).sum().alias("total"))
        .sort("total", descending=True)
    )


# 4. Un main que imprime el resultado, para compararlo con `python ventas_ia.py`.
if __name__ == "__main__":
    filas = lee_filas(RUTA)
    buenas = valida(filas)
    print(f"{len(buenas)} de {len(filas)} filas válidas")
    print(total_por_tienda(buenas))
