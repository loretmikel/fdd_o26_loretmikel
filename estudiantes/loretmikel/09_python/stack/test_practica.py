"""Las pruebas de practica.py. Corre: pytest -v --no-header test_practica.py

Cuatro casos: la fila buena de la plantilla, una fila sucia (el precio "abc"
que trae ventas.csv), el caso borde de cantidad = 0 (gt, no ge) y la tabla
vacía, que sin el esquema explícito tronaba en group_by.
"""

import polars as pl
import pytest
from pydantic import ValidationError

try:
    from practica import Venta, total_por_tienda
except ImportError:
    pytest.skip("practica.py todavía no define Venta", allow_module_level=True)

# Una fila buena de ventas.csv, tal como llega del CSV: todo es texto.
BUENA = {
    "fecha": "2025-01-03",
    "tienda": "Centro",
    "producto": "P001",
    "cantidad": "3",
    "precio": "120.50",
}


def test_fila_buena_se_convierte() -> None:
    venta = Venta.model_validate(BUENA)
    assert venta.cantidad == 3
    assert venta.precio == 120.5


def test_fila_sucia_precio_abc_se_rechaza() -> None:
    # La fila de Sur en ventas.csv: "abc" no es un float, y el error dice el campo.
    with pytest.raises(ValidationError, match="precio"):
        Venta.model_validate({**BUENA, "precio": "abc"})


def test_borde_cantidad_cero_se_rechaza_y_uno_entra() -> None:
    # gt=0 es estrictamente mayor: el 0 queda justo del lado malo del borde.
    with pytest.raises(ValidationError, match="greater_than"):
        Venta.model_validate({**BUENA, "cantidad": "0"})
    assert Venta.model_validate({**BUENA, "cantidad": "1"}).cantidad == 1


def test_borde_sin_ventas_da_tabla_vacia_con_columnas() -> None:
    # Sin ventas válidas no hay filas, pero la tabla conserva sus dos columnas.
    tabla = total_por_tienda([])
    assert tabla.shape == (0, 2)
    assert tabla.columns == ["tienda", "total"]


def test_total_por_tienda_suma_y_ordena() -> None:
    ventas = [
        Venta.model_validate(BUENA),  # Centro: 3 × 120.50 = 361.50
        Venta.model_validate({**BUENA, "tienda": "Norte", "cantidad": "1"}),  # 120.50
        Venta.model_validate({**BUENA, "cantidad": "2", "precio": "10"}),  # Centro +20
    ]
    tabla = total_por_tienda(ventas)
    assert tabla["tienda"].to_list() == ["Centro", "Norte"]
    assert tabla["total"].to_list() == pytest.approx([381.5, 120.5])
    assert tabla.schema["total"] == pl.Float64
