from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_roles
from app.models import FinancialRecord, RecordType, User, UserRole
from app.schemas import RecordCreate, RecordOut, RecordUpdate

router = APIRouter(prefix="/records", tags=["Financial Records"])


@router.post("/", response_model=RecordOut, status_code=status.HTTP_201_CREATED)
def create_record(
    payload: RecordCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin)),
) -> FinancialRecord:
    record = FinancialRecord(
        amount=payload.amount,
        record_type=payload.record_type,
        category=payload.category,
        date=payload.date,
        notes=payload.notes,
        created_by=user.id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/", response_model=list[RecordOut])
def list_records(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin, UserRole.analyst)),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    category: str | None = Query(default=None),
    record_type: RecordType | None = Query(default=None),
) -> list[FinancialRecord]:
    query = db.query(FinancialRecord)

    if date_from:
        query = query.filter(FinancialRecord.date >= date_from)
    if date_to:
        query = query.filter(FinancialRecord.date <= date_to)
    if category:
        query = query.filter(FinancialRecord.category.ilike(f"%{category.strip()}%"))
    if record_type:
        query = query.filter(FinancialRecord.record_type == record_type)

    return query.order_by(FinancialRecord.date.desc(), FinancialRecord.id.desc()).offset(skip).limit(limit).all()


@router.get("/{record_id}", response_model=RecordOut)
def get_record(
    record_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin, UserRole.analyst)),
) -> FinancialRecord:
    record = db.query(FinancialRecord).filter(FinancialRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return record


@router.put("/{record_id}", response_model=RecordOut)
def update_record(
    record_id: int,
    payload: RecordUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
) -> FinancialRecord:
    record = db.query(FinancialRecord).filter(FinancialRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(record, field, value)

    db.commit()
    db.refresh(record)
    return record


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
) -> None:
    record = db.query(FinancialRecord).filter(FinancialRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")

    db.delete(record)
    db.commit()
