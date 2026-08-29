from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_alembic_migrations_render_full_postgresql_sql_chain(tmp_path):
    output = tmp_path / "schema.sql"
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head", "--sql"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    output.write_text(result.stdout)
    sql = output.read_text()
    assert "CREATE TABLE orders" in sql
    assert "CREATE TABLE partner_settlements" in sql
    assert "CREATE TABLE rider_remittance_allocations" in sql
    assert "CREATE TABLE delivery_quotes" in sql
    assert "CREATE TYPE refundpayer" in sql
    assert "uq_partner_cod_credit_per_order" in sql
    assert "b5e1f7c3a692" in sql
