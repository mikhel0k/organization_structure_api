import logging
from typing import Literal

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.department import Department
from app.repositories.department import DepartmentRepository
from app.repositories.employee import EmployeeRepository
from app.schemas.department import (
    DepartmentCreate,
    DepartmentRead,
    DepartmentTreeNode,
    DepartmentUpdate,
)
from app.schemas.employee import EmployeeCreate, EmployeeRead

logger = logging.getLogger(__name__)


class DepartmentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.department_repo = DepartmentRepository(db)
        self.employee_repo = EmployeeRepository(db)

    def create_department(self, data: DepartmentCreate) -> DepartmentRead:
        if data.parent_id is not None:
            parent = self.department_repo.get_by_id(data.parent_id)
            if parent is None:
                raise NotFoundError("Parent department not found")

        if self.department_repo.get_by_name_and_parent(data.name, data.parent_id):
            raise ConflictError(
                "Department with this name already exists under the same parent",
            )

        department = self.department_repo.create(data.name, data.parent_id)
        self.db.commit()
        logger.info("Created department id=%s name=%s", department.id, department.name)
        return DepartmentRead.model_validate(department)

    def create_employee(
        self,
        department_id: int,
        data: EmployeeCreate,
    ) -> EmployeeRead:
        department = self.department_repo.get_by_id(department_id)
        if department is None:
            raise NotFoundError("Department not found")

        employee = self.employee_repo.create(
            department_id=department_id,
            full_name=data.full_name,
            position=data.position,
            hired_at=data.hired_at,
        )
        self.db.commit()
        logger.info(
            "Created employee id=%s in department id=%s",
            employee.id,
            department_id,
        )
        return EmployeeRead.model_validate(employee)

    def get_department_tree(
        self,
        department_id: int,
        depth: int = 1,
        include_employees: bool = True,
    ) -> DepartmentTreeNode:
        if depth < 1 or depth > 5:
            raise ValidationError("depth must be between 1 and 5")

        department = self.department_repo.get_with_tree(
            department_id,
            depth,
            include_employees,
        )
        if department is None:
            raise NotFoundError("Department not found")

        return self._build_tree_node(department, depth, include_employees)

    def _build_tree_node(
        self,
        department: Department,
        depth: int,
        include_employees: bool,
    ) -> DepartmentTreeNode:
        employees = []
        if include_employees:
            sorted_employees = sorted(
                department.employees,
                key=lambda employee: (employee.created_at, employee.full_name),
            )
            employees = [EmployeeRead.model_validate(e) for e in sorted_employees]

        children = []
        if depth > 1:
            sorted_children = sorted(department.children, key=lambda child: child.name)
            children = [
                self._build_tree_node(child, depth - 1, include_employees)
                for child in sorted_children
            ]

        return DepartmentTreeNode(
            department=DepartmentRead.model_validate(department),
            employees=employees,
            children=children,
        )

    def update_department(
        self,
        department_id: int,
        data: DepartmentUpdate,
    ) -> DepartmentRead:
        department = self.department_repo.get_by_id(department_id)
        if department is None:
            raise NotFoundError("Department not found")

        fields_set = data.model_fields_set
        new_name = data.name if "name" in fields_set else None
        parent_id_set = "parent_id" in fields_set
        new_parent_id = data.parent_id if parent_id_set else department.parent_id

        if parent_id_set:
            if new_parent_id == department_id:
                raise ConflictError("Department cannot be its own parent")

            if new_parent_id is not None:
                parent = self.department_repo.get_by_id(new_parent_id)
                if parent is None:
                    raise NotFoundError("Parent department not found")

                descendants = self.department_repo.get_descendant_ids(department_id)
                if new_parent_id in descendants:
                    raise ConflictError(
                        "Cannot move department into its own subtree",
                    )

        target_name = new_name if new_name is not None else department.name
        target_parent_id = new_parent_id if parent_id_set else department.parent_id

        existing = self.department_repo.get_by_name_and_parent(
            target_name,
            target_parent_id,
            exclude_id=department_id,
        )
        if existing is not None:
            raise ConflictError(
                "Department with this name already exists under the same parent",
            )

        updated = self.department_repo.update(
            department,
            name=new_name,
            parent_id=new_parent_id,
            parent_id_set=parent_id_set,
        )
        self.db.commit()
        logger.info("Updated department id=%s", department_id)
        return DepartmentRead.model_validate(updated)

    def delete_department(
        self,
        department_id: int,
        mode: Literal["cascade", "reassign"],
        reassign_to_department_id: int | None = None,
    ) -> None:
        department = self.department_repo.get_by_id(department_id)
        if department is None:
            raise NotFoundError("Department not found")

        if mode == "reassign":
            if reassign_to_department_id is None:
                raise ValidationError(
                    "reassign_to_department_id is required when mode=reassign",
                )
            if reassign_to_department_id == department_id:
                raise ValidationError(
                    "reassign_to_department_id must differ from the deleted department",
                )

            target = self.department_repo.get_by_id(reassign_to_department_id)
            if target is None:
                raise NotFoundError("Target department for reassignment not found")

            descendants = self.department_repo.get_descendant_ids(department_id)
            if reassign_to_department_id in descendants | {department_id}:
                raise ConflictError(
                    "Cannot reassign employees to a department inside the deleted subtree",
                )

            self.department_repo.reassign_employees(
                department_id,
                reassign_to_department_id,
            )
            self.department_repo.move_children_to_parent(
                department,
                department.parent_id,
            )
            self.department_repo.delete(department)
        else:
            self.department_repo.delete(department)

        self.db.commit()
        logger.info("Deleted department id=%s mode=%s", department_id, mode)
