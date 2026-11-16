from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.address import Address
from app.schemas.address import AddressCreate, AddressOut, AddressUpdate

router = APIRouter(prefix="/api/v1/addresses", tags=["Addresses"])

@router.post("", response_model=AddressOut, status_code=status.HTTP_201_CREATED)
def create_address(payload: AddressCreate, db: Session = Depends(get_db)):
    obj = Address(**payload.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@router.get("", response_model=list[AddressOut])
def list_addresses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Address).offset(skip).limit(min(limit, 200)).all()

@router.get("/{address_id}", response_model=AddressOut)
def get_address(address_id: int, db: Session = Depends(get_db)):
    obj = db.get(Address, address_id)
    if not obj: raise HTTPException(404, "Address not found")
    return obj

@router.patch("/{address_id}", response_model=AddressOut)
def update_address(address_id: int, payload: AddressUpdate, db: Session = Depends(get_db)):
    obj = db.get(Address, address_id)
    if not obj: raise HTTPException(404, "Address not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit(); db.refresh(obj)
    return obj

@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(address_id: int, db: Session = Depends(get_db)):
    obj = db.get(Address, address_id)
    if not obj: raise HTTPException(404, "Address not found")
    if obj.stations:
        raise HTTPException(409, "Address is assigned to a charging station")
    db.delete(obj); db.commit()
