import uuid

from pydantic import BaseModel, model_validator


class CustomerCreate(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None

    @model_validator(mode="after")
    def check_contact(self):
        if not self.email and not self.phone:
            raise ValueError("Either email or phone must be provided")
        return self


class CustomerOut(BaseModel):
    id: uuid.UUID
    name: str
    email: str | None
    phone: str | None

    model_config = {"from_attributes": True}
