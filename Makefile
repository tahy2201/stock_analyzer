.PHONY: format lint typecheck check test clean help

# デフォルトターゲット
help:
	@echo "Available targets:"
	@echo "  format     - Format code with ruff"
	@echo "  lint       - Lint code with ruff"
	@echo "  typecheck  - Type check with mypy"
	@echo "  check      - Run all checks (lint + typecheck)"
	@echo "  test       - Run tests with pytest"
	@echo "  clean      - Clean up temporary files"
	@echo "  help       - Show this help message"

# コードフォーマット
format:
	uv run ruff format .

# リンティング
lint:
	uv run ruff check .

# リンティング（自動修正付き）
lint-fix:
	uv run ruff check --fix .

# importソート
sort-imports:
	uv run ruff check --select I --fix .

# 型チェック
typecheck:
	uv run mypy .

# 全体チェック（リンティング + 型チェック）
check: lint typecheck
	@echo "All checks passed!"

# テスト実行
test:
	uv run pytest

# テスト実行（カバレッジ付き）
test-cov:
	uv run pytest --cov=. --cov-report=html --cov-report=term-missing

# 一時ファイルの削除
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/

# CI用：全チェック + テスト
ci: check test
	@echo "CI checks completed!"

# 開発用：フォーマット + チェック
dev: format check
	@echo "Development checks completed!"