from datetime import date as dt_date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import RecordType, UserRole


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    full_name: str = Field(min_length=2, max_length=100)
    role: UserRole
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    role: UserRole | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class RecordBase(BaseModel):
    amount: float = Field(gt=0)
    record_type: RecordType
    category: str = Field(min_length=2, max_length=100)
    date: dt_date
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str) -> str:
        return value.strip().title()


class RecordCreate(RecordBase):
    pass


class RecordUpdate(BaseModel):
    amount: float | None = Field(default=None, gt=0)
    record_type: RecordType | None = None
    category: str | None = Field(default=None, min_length=2, max_length=100)
    date: dt_date | None = None
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip().title()


class RecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: float
    record_type: RecordType
    category: str
    date: dt_date
    notes: str | None
    created_by: int
    created_at: datetime
    updated_at: datetime


class CategorySummary(BaseModel):
    category: str
    total: float


class TrendPoint(BaseModel):
    period: str
    income: float
    expense: float


class DashboardSummary(BaseModel):
    total_income: float
    total_expense: float
    net_balance: float
    category_totals: list[CategorySummary]
    recent_activity: list[RecordOut]
    monthly_trends: list[TrendPoint]
