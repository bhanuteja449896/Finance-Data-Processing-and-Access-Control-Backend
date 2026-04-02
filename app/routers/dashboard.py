from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_roles
from app.models import FinancialRecord, RecordType, User, UserRole
from app.schemas import CategorySummary, DashboardSummary, RecordOut, TrendPoint

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin, UserRole.analyst, UserRole.viewer)),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
) -> DashboardSummary:
    query = db.query(FinancialRecord)
    if date_from:
        query = query.filter(FinancialRecord.date >= date_from)
    if date_to:
        query = query.filter(FinancialRecord.date <= date_to)

    income_total = query.filter(FinancialRecord.record_type == RecordType.income).with_entities(
        func.coalesce(func.sum(FinancialRecord.amount), 0)
    ).scalar()
    expense_total = query.filter(FinancialRecord.record_type == RecordType.expense).with_entities(
        func.coalesce(func.sum(FinancialRecord.amount), 0)
    ).scalar()

    category_rows = (
        query.with_entities(FinancialRecord.category, func.sum(FinancialRecord.amount))
        .group_by(FinancialRecord.category)
        .order_by(func.sum(FinancialRecord.amount).desc())
        .all()
    )
    category_totals = [CategorySummary(category=row[0], total=float(row[1])) for row in category_rows]

    recent_rows = query.order_by(FinancialRecord.date.desc(), FinancialRecord.id.desc()).limit(10).all()
    recent_activity = [RecordOut.model_validate(row) for row in recent_rows]

    monthly_rows = (
        query.with_entities(
            func.strftime("%Y-%m", FinancialRecord.date).label("period"),
            FinancialRecord.record_type,
            func.sum(FinancialRecord.amount),
        )
        .group_by("period", FinancialRecord.record_type)
        .order_by("period")
        .all()
    )

    monthly_map: dict[str, dict[str, float]] = {}
    for period, record_type, amount in monthly_rows:
        month_values = monthly_map.setdefault(period, {"income": 0.0, "expense": 0.0})
        month_values[str(record_type.value)] = float(amount)

    monthly_trends = [
        TrendPoint(period=period, income=values["income"], expense=values["expense"])
        for period, values in sorted(monthly_map.items())
    ]

    return DashboardSummary(
        total_income=float(income_total),
        total_expense=float(expense_total),
        net_balance=float(income_total) - float(expense_total),
        category_totals=category_totals,
        recent_activity=recent_activity,
        monthly_trends=monthly_trends,
    )
