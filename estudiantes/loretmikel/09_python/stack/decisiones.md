# Decisiones: de ventas_ia.py a practica.py

## Qué cambié, por qué y qué patrón

Al menos tres filas. El patrón es uno de los ocho de la página «Patrones y
el stack escrito».

| Qué cambié | Por qué | Qué patrón |
|---|---|---|
| El contrato `Venta`: `class Config` + un validador en Python (Pydantic v1) → `model_config = ConfigDict(str_strip_whitespace=True)` y `cantidad: int = Field(gt=0)`, `precio: float = Field(gt=0)` (v2) | La sintaxis v1 avisa `PydanticDeprecatedSince20` y desaparece en v3; el `pyproject.toml` convierte ese aviso en error en las pruebas. Además, un validador en Python corre en el intérprete por cada fila; `Field(gt=0)` lo revisa `pydantic-core`, en Rust, y la regla queda en el contrato (y en el JSON Schema) en vez de escondida en un método | Fuera del intérprete es rápido |
| La frontera: `Venta(**fila).dict()` por fila, y `cantidad: Optional[int]` con `None` permitido → `Venta.model_validate(fila)` una sola vez por fila, que devuelve el objeto `Venta` y se queda así; `cantidad: int` sin `None` | `.dict()` es v1 y, peor, tira la garantía: convertía el objeto validado otra vez en un `dict` que ya nadie revisa. Validar cuesta 5–10× un `dict` (A.8), así que se paga una vez, en la frontera, y adentro `total_por_tienda` confía en que recibe `Venta` ya buenas. Qué fila entra lo decide el contrato, no un `if` suelto: una `cantidad` vacía o `≤ 0` no es «opcional», es inválida | Más garantías, más costo |
| La suma: pandas con `df.apply(lambda fila: fila["cantidad"] * fila["precio"], axis=1)` y `groupby().sum().sort_values()` → Polars con `group_by("tienda").agg((pl.col("cantidad") * pl.col("precio")).sum()).sort("total", descending=True)` | El `lambda` del `apply` es un `for` de Python fila por fila; `cantidad * precio` es una expresión sobre dos columnas enteras y Polars la ejecuta en Rust, en paralelo. Los totales salen idénticos a los de `python ventas_ia.py` (Santa Fe 3307.14 … Poniente 63.00), sólo cambia dónde corre el trabajo | Fuera del intérprete es rápido |
| La tabla: `pd.DataFrame(buenas)` que infiere tipos → `pl.DataFrame(list(ventas), schema=ESQUEMA)` con `Date`, `String`, `Int64`, `Float64` declarados una vez | Con tipos inferidos, los textos quedan como `object` y un entero con huecos se vuelve `float`; con el esquema explícito cada columna tiene el tipo que ya decidió el contrato. Y el caso borde: sin esquema, una lista vacía de ventas da un DataFrame de 0 × 0 y `group_by("tienda")` truena con `ColumnNotFoundError`; con esquema devuelve una tabla vacía con sus columnas (lo prueba `test_borde_sin_ventas_da_tabla_vacia_con_columnas`) | El tipo decide la memoria |

Dos cambios menores que no son uno de los ocho patrones, pero que `ruff` (regla `UP`) y la pregunta 1 de «elegir una librería» piden: `typing.Dict/List/Optional` → `dict[str, str]`, `list[Venta]`, `int`; y `os.path.join(os.path.dirname(os.path.abspath(__file__)), …)` → `Path(__file__).parent / "ventas.csv"`, que ya lo hace la biblioteca estándar.

## Salida de pytest

Pega la salida completa de `pytest -v --no-header test_practica.py`,
corrido en `stack/`. `--no-header` quita las líneas con la ruta de tu máquina.

```text
============================= test session starts ==============================
collecting ... collected 5 items

test_practica.py::test_fila_buena_se_convierte PASSED                    [ 20%]
test_practica.py::test_fila_sucia_precio_abc_se_rechaza PASSED           [ 40%]
test_practica.py::test_borde_cantidad_cero_se_rechaza_y_uno_entra PASSED [ 60%]
test_practica.py::test_borde_sin_ventas_da_tabla_vacia_con_columnas PASSED [ 80%]
test_practica.py::test_total_por_tienda_suma_y_ordena PASSED             [100%]

============================== 5 passed in 0.17s ===============================
```

## Salida de ruff

Pega la salida de `ruff check practica.py test_practica.py`.

```text
All checks passed!
```

## Salida de mypy

Pega la salida de `mypy practica.py`.

```text
Success: no issues found in 1 source file
```
