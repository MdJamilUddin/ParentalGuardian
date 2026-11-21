from app.config.settings import normalize_database_url as norm

PG = "postgresql+psycopg2://u:p@h:5432/db"


def test_hosting_provider_urls_are_normalised():
    assert norm("postgres://u:p@h:5432/db") == PG
    assert norm("postgresql://u:p@h:5432/db") == PG


def test_other_urls_are_left_alone():
    assert norm(PG) == PG
    assert norm("sqlite:///./guardian.db") == "sqlite:///./guardian.db"
