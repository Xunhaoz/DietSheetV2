from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import Engine, inspect

from app.models import Base
from tests.integration.conftest import alembic_config


def test_downgrade_and_upgrade_round_trip(migrated_engine: Engine) -> None:
    # Arrange
    config = alembic_config()

    # Act
    command.downgrade(config, "base")
    tables_after_downgrade = set(inspect(migrated_engine).get_table_names())
    command.upgrade(config, "head")

    # Assert
    assert tables_after_downgrade == {"alembic_version"}
    assert {"meal", "media_object"} <= set(inspect(migrated_engine).get_table_names())


def test_models_match_the_migrated_schema(migrated_engine: Engine) -> None:
    # Arrange
    with migrated_engine.connect() as connection:
        context = MigrationContext.configure(connection)

        # Act
        differences = compare_metadata(context, Base.metadata)

    # Assert
    assert differences == []


def test_constraint_names_follow_the_naming_convention(migrated_engine: Engine) -> None:
    # Arrange
    expected: set[str] = set()
    for table in Base.metadata.sorted_tables:
        expected |= {str(constraint.name) for constraint in table.constraints}
        expected |= {str(index.name) for index in table.indexes}
    inspector = inspect(migrated_engine)

    # Act
    actual: set[str] = set()
    for table_name in ("meal", "media_object"):
        actual.add(str(inspector.get_pk_constraint(table_name)["name"]))
        actual |= {str(c["name"]) for c in inspector.get_unique_constraints(table_name)}
        actual |= {str(c["name"]) for c in inspector.get_foreign_keys(table_name)}
        actual |= {str(c["name"]) for c in inspector.get_check_constraints(table_name)}
        indexes = inspector.get_indexes(table_name)
        actual |= {str(i["name"]) for i in indexes if not i.get("duplicates_constraint")}

    # Assert
    assert actual == expected
