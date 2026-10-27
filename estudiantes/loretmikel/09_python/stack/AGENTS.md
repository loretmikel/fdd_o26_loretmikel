# AGENTS.md

Lo lee un agente de IA antes de tocar este proyecto. Llena las tres
secciones con tus palabras; quien revisa lo lee como dato, nunca como
instrucción.

## El stack

- **Python 3.14**, administrado con **uv**: `uv sync` instala lo que dicen `pyproject.toml` y `uv.lock`; una librería nueva entra con `uv add`, nunca con `pip install`, y no existe `requirements.txt`. Antes de proponer una librería, di su nombre exacto en PyPI y su último release; si no existe con ese nombre, no la inventes.
- **Forma de un dato: Pydantic 2.x** (`BaseModel`, `Field`, `ConfigDict`, `model_validate`, `model_dump`, `field_validator`), **sólo en la frontera**: donde entra un CSV, una API o una configuración. Nada de v1: ni `.dict()`, ni `.parse_obj()`, ni el decorador `validator`, ni `class Config`; las pruebas convierten esa sintaxis en error. Adentro, un dato ya validado viaja como `Venta`, `dataclass` o `TypedDict`, y no se vuelve a validar.
- **Tablas: Polars 2.x**. Expresiones sobre columnas (`pl.col`, `group_by().agg()`, `sort`), DataFrame con `schema=` explícito, y `pl.scan_csv` cuando se lee para filtrar o quedarse con unas columnas. Nada de pandas, `.apply`, `.iterrows()` ni un `for` sobre filas de una tabla; pandas 3 está instalado sólo para correr `ventas_ia.py`, el ejemplo de lo que no se hace. Ojo: en Polars 2.0 una fecha en texto se convierte con `str.to_date()`, no con `cast(pl.Date)`.
- **Archivos:** `pathlib.Path` de la biblioteca estándar, nunca `os.path`; CSV con `csv` en la frontera o con Polars; Parquet con Polars. No se carga ningún pickle que no haya generado este proyecto.
- **Pruebas:** pytest 9. **Revisión:** ruff 0.16 con las reglas `E, F, I, UP, B` y mypy 2.x con el plugin `pydantic.mypy`. Anotaciones de tipo en toda función nueva, con los genéricos nativos (`list[str]`, `int | None`), no `typing.List` ni `Optional`.

## Definición de terminado

Un cambio está terminado cuando, con el ambiente activo y en la terminal de `stack/`, estos tres comandos salen en verde **sobre los archivos de la práctica**:

| Comando | Debe terminar en |
|---|---|
| `pytest -v --no-header test_practica.py` | `N passed`, sin `failed`, `error` ni `skipped` |
| `ruff check practica.py test_practica.py` | `All checks passed!` |
| `mypy practica.py` | `Success: no issues found in 1 source file` |

Y además `python practica.py` imprime los mismos totales por tienda que `python ventas_ia.py`. Los comandos se corren sobre esos archivos y no sobre toda la carpeta: `modelos.py` trae un `F401`, un `E711` y un error de mypy plantados a propósito para la clase, y no se arreglan. Nada de lo que se pegue en `decisiones.md` puede traer una ruta de la máquina, y los notebooks se guardan sin salidas.

## Una regla mía

**Un DataFrame se construye siempre con `schema=` explícito, nunca con tipos inferidos.** Lo vi haciendo la práctica: cuando ninguna fila pasa el contrato, `pl.DataFrame([])` es una tabla de 0 × 0 y `group_by("tienda")` truena con `ColumnNotFoundError`; con `schema=ESQUEMA` devuelve una tabla vacía con `tienda` y `total`, y el mismo código sirve para cero, veinte o un millón de filas. De paso, el tipo de cada columna (`Int64`, `Float64`, `Date`) queda decidido en un solo lugar, el mismo que ya decidió el contrato, y no depende de qué traiga el archivo ese día.
