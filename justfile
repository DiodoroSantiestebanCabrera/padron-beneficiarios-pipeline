# justfile — raíz del proyecto, sin extensión
default:
    just --list

init:
    mkdir -p src/bronze src/silver src/gold src/utils tests docs notebooks data/synthetic
    touch src/bronze/ingesta.py src/silver/limpieza.py src/silver/geografia.py src/gold/modelo_estrella.py
    touch tests/test_limpieza.py docs/.gitkeep notebooks/.gitkeep data/synthetic/.gitkeep

lint:
    uv run ruff check . --fix
    uv run ruff format .

test:
    uv run pytest

ci: lint test