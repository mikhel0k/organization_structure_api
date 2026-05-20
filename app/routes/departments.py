import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.department import (
    DepartmentCreate,
    DepartmentRead,
    DepartmentTreeNode,
    DepartmentUpdate,
)
from app.schemas.employee import EmployeeCreate, EmployeeRead
from app.services.department import DepartmentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/departments", tags=["departments"])


def get_department_service(db: Session = Depends(get_db)) -> DepartmentService:
    return DepartmentService(db)


@router.post(
    "/",
    response_model=DepartmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create department",
)
def create_department(
    data: DepartmentCreate,
    service: Annotated[DepartmentService, Depends(get_department_service)],
) -> DepartmentRead:
    return service.create_department(data)


@router.post(
    "/{department_id}/employees/",
    response_model=EmployeeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create employee in department",
)
def create_employee(
    department_id: int,
    data: EmployeeCreate,
    service: Annotated[DepartmentService, Depends(get_department_service)],
) -> EmployeeRead:
    return service.create_employee(department_id, data)


@router.get(
    "/{department_id}",
    response_model=DepartmentTreeNode,
    summary="Get department with subtree",
)
def get_department(
    department_id: int,
    service: Annotated[DepartmentService, Depends(get_department_service)],
    depth: Annotated[int, Query(ge=1, le=5)] = 1,
    include_employees: bool = True,
) -> DepartmentTreeNode:
    return service.get_department_tree(
        department_id,
        depth=depth,
        include_employees=include_employees,
    )


@router.patch(
    "/{department_id}",
    response_model=DepartmentRead,
    summary="Update department",
)
def update_department(
    department_id: int,
    data: DepartmentUpdate,
    service: Annotated[DepartmentService, Depends(get_department_service)],
) -> DepartmentRead:
    return service.update_department(department_id, data)


@router.delete(
    "/{department_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete department",
)
def delete_department(
    department_id: int,
    service: Annotated[DepartmentService, Depends(get_department_service)],
    mode: Literal["cascade", "reassign"] = "cascade",
    reassign_to_department_id: int | None = None,
) -> None:
    service.delete_department(
        department_id,
        mode=mode,
        reassign_to_department_id=reassign_to_department_id,
    )
