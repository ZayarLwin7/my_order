import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class TransactionType(str, enum.Enum):
    collection = "collection"      # rider collected COD/fee on delivery
    remittance = "remittance"      # rider paid platform during settlement
    adjustment = "adjustment"      # manual Admin correction (dispute, etc.)


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rider_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)  # positive = adds to balance, negative = reduces it
    reference = Column(String, nullable=True, unique=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class RiderRemittanceAllocation(Base):
    __tablename__ = "rider_remittance_allocations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    remittance_transaction_id = Column(UUID(as_uuid=True), ForeignKey("wallet_transactions.id"), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    cod_amount = Column(Numeric(12, 2), nullable=False, default=0)
    delivery_fee_amount = Column(Numeric(12, 2), nullable=False, default=0)
    allocated_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
