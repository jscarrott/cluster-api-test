from fastapi import FastAPI, HTTPException, status, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlmodel import Field, Session, SQLModel, create_engine, select, Column
from pydantic import InstanceOf, ValidationError, model_validator, field_validator, ValidationInfo, ConfigDict, BaseModel, WrapValidator
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import JSONB
from typing import Any, Dict, List, Self, Annotated
import json
from collections.abc import Callable
from .lenient_list import LenientList

class EventBase(SQLModel):
    event_id: str | None = Field(default=None, primary_key=True)
    type: str = Field(index=True)
    event: Dict[str, Any] = Field(default=None, sa_column=Column(JSONB))
    timestamp: datetime = Field(default=None, index=True)


    @model_validator(mode='after')
    def check_location(self) -> Self:
        if self.type == "system":
            location = self.event.get("location", "")
            if location != "europe" or location != "us":
                raise ValueError('Unsupported location for system event')
        return self

    @model_validator(mode='after')
    def check_in_past(self) -> Self:
        if self.timestamp > datetime.now(timezone.utc):
            raise ValueError('Must not be in the future')
        return self

class Event(EventBase, table=True):
    pass

class EventCreate(EventBase, table=False):
    pass

class EventList(BaseModel):
    events: LenientList[EventCreate]
    
    
postgres_url = "postgresql+psycopg://test:123456789@api-test-postgresql/test"

engine = create_engine(postgres_url)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


app = FastAPI()
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )


@app.post("/events/")
def create_event(events: LenientList[EventCreate]):
    if len(events) > 1000:
         raise HTTPException(status_code=400, detail=f"Too many events included in the requests MAX=1000 GOT={len(events)}")
    
    with Session(engine) as session:
        for event in events:
            event_sql =  Event.model_validate(event)
            session.add(event_sql)
            try:
                session.commit()
            except Exception as e:
                # Would do better error handling
                raise HTTPException(status_code=400, detail="Event already exists with this ID")

    if len(events.errors):
        error_result = []
        for error in events.errors:
            error_result.append(error.errors(include_url=False))
        return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(error_result),
        )



@app.get("/events/{id}")
def read_event(id: str):
    with Session(engine) as session:
        event = session.exec(select(Event).where(Event.event_id == id)).first()
        return event
