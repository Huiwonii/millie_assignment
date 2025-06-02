from enum import Enum


class ChoiceEnum(Enum):
    @classmethod
    def choices(cls):
        return [(choice.value, choice.name) for choice in cls]


class TargetType(ChoiceEnum):
    PRODUCT = "PRODUCT"
    USER = "USER"
    ALL = "ALL"


class DiscountType(ChoiceEnum):
    PERCENTAGE = "PERCENTAGE"
    FIXED = "FIXED"


class CouponStatus(ChoiceEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    EXPIRED = "EXPIRED"
