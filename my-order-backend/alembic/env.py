import sys
import os
sys.path.append(os.getcwd())

from logging.config import fileConfig
from sqlalchemy import create_engine
from sqlalchemy import pool
from alembic import context

from app.config import settings
from app.database import Base
from app.models.user import User
from app.models.rider import RiderProfile, RiderApplication
from app.models.order import Order, OrderTrackingLog
from app.models.wallet import RiderRemittanceAllocation, WalletTransaction
from app.models.dispute import Dispute
from app.models.partner import PartnerApplication, PartnerProfile, PartnerLedgerEntry, PartnerSettlement
from app.models.rider_earnings import RiderCompensationRate, RiderEarning, RiderPayout
from app.models.pricing import DeliveryQuote, DeliveryZone, ItemSizeRate

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(settings.database_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
