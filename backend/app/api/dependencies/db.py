from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.session import get_db

# FastAPI will resolve Depends(get_db) per-request even through Annotated alias.
DBSession = Annotated[Session, Depends(get_db)]
