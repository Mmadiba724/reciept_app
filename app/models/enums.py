import enum


class UserRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    staff = "staff"


class ReceiptStatus(str, enum.Enum):
    issued = "issued"
    voided = "voided"
    refunded = "refunded"


class DeliveryChannel(str, enum.Enum):
    email = "email"
    sms = "sms"


class DeliveryStatus(str, enum.Enum):
    queued = "queued"
    sent = "sent"
    delivered = "delivered"
    bounced = "bounced"
    failed = "failed"
    opened = "opened"


class PlanTier(str, enum.Enum):
    free_trial = "free_trial"
    starter = "starter"
    growth = "growth"
    enterprise = "enterprise"


class PaymentMethodType(str, enum.Enum):
    cash = "cash"
    bank_transfer = "bank_transfer"
    mobile_money = "mobile_money"
    cheque = "cheque"
    other = "other"
