from enum import Enum


class ChoiceEnum(Enum):
    @classmethod
    def choices(cls):
        return [(choice.value, choice.name) for choice in cls]


class Feature(ChoiceEnum):
    MONTHLY_RECOMMEND = "MONTHLY_RECOMMEND"
    NEW_ARRIVAL = "NEW_ARRIVAL"
    BEST_SELLER = "BEST_SELLER"


class Category(ChoiceEnum):
    FICTION = "FICTION"
    NON_FICTION = "NON_FICTION"
    SCIENCE = "SCIENCE"
    TECHNOLOGY = "TECHNOLOGY"
    SELF_HELP = "SELF_HELP"
    BUSINESS = "BUSINESS"
    HISTORY = "HISTORY"
    BIOGRAPHY = "BIOGRAPHY"
    PHILOSOPHY = "PHILOSOPHY"
    RELIGION = "RELIGION"
    OTHER = "OTHER"


class ProductStatus(ChoiceEnum):
    ACTIVE = "ACTIVE"
    SOLD_OUT = "SOLD_OUT"
    DISCONTINUED = "DISCONTINUED"


class VisibilityStatus(ChoiceEnum):
    VISIBLE = "VISIBLE"
    HIDDEN = "HIDDEN"