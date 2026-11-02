
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, model_validator


class ConstraintType(str, Enum):
    FRONT_SETBACK = "front_setback"
    REAR_SETBACK = "rear_setback"
    LEFT_SETBACK = "left_setback"
    RIGHT_SETBACK = "right_setback"
    MAX_HEIGHT = "max_height"
    MAX_SITE_COVERAGE = "max_site_coverage"


class VerificationStatus(str, Enum):
    EXTRACTED = "extracted"
    NEEDS_HUMAN_REVIEW = "needs_human_review"
    VERIFIED = "verified"
    REJECTED = "rejected"
    CONFLICTING = "conflicting"
    UNRESOLVED = "unresolved"


class RegulationConstraint(BaseModel):
    """
    A structured regulation constraint with source provenance.

    A constraint is not legally verified merely because
    an AI model extracted it.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    constraint_id: str = Field(min_length=1)
    constraint_type: ConstraintType

    value: Optional[float] = Field(default=None, gt=0)
    unit: Optional[str] = None

    document_id: str = Field(min_length=1)
    page_number: int = Field(gt=0)
    clause_reference: Optional[str] = None
    source_excerpt: str = Field(min_length=1)

    applicability: Optional[str] = None
    exceptions: list[str] = Field(default_factory=list)

    status: VerificationStatus = (
        VerificationStatus.NEEDS_HUMAN_REVIEW
    )

    verification_notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_constraint(self):
        if self.value is None and self.status == VerificationStatus.VERIFIED:
            raise ValueError(
                "A constraint without a value cannot be verified."
            )

        if (
            self.constraint_type == ConstraintType.MAX_SITE_COVERAGE
            and self.value is not None
            and not 0 < self.value <= 100
        ):
            raise ValueError(
                "Maximum site coverage must be greater than 0 "
                "and at most 100 percent."
            )

        if self.value is not None and not self.unit:
            raise ValueError(
                "A numerical constraint must specify its unit."
            )

        return self
