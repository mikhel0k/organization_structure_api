from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.department import Department
from app.models.employee import Employee
from app.repositories.base import BaseRepository


class DepartmentRepository(BaseRepository[Department]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Department)

    def get_by_name_and_parent(
        self,
        name: str,
        parent_id: int | None,
        exclude_id: int | None = None,
    ) -> Department | None:
        stmt = select(Department).where(
            Department.name == name,
        )
        if parent_id is None:
            stmt = stmt.where(Department.parent_id.is_(None))
        else:
            stmt = stmt.where(Department.parent_id == parent_id)
        if exclude_id is not None:
            stmt = stmt.where(Department.id != exclude_id)
        return self.db.scalar(stmt)

    def create(self, name: str, parent_id: int | None) -> Department:
        return self.add(Department(name=name, parent_id=parent_id))

    def update(
        self,
        department: Department,
        *,
        name: str | None = None,
        parent_id: int | None = None,
        parent_id_set: bool = False,
    ) -> Department:
        if name is not None:
            department.name = name
        if parent_id_set:
            department.parent_id = parent_id
        self.db.flush()
        self.db.refresh(department)
        return department

    def get_children(self, department_id: int) -> list[Department]:
        stmt = select(Department).where(Department.parent_id == department_id)
        return list(self.db.scalars(stmt).all())

    def get_descendant_ids(self, department_id: int) -> set[int]:
        descendants: set[int] = set()
        queue = [department_id]
        while queue:
            current_id = queue.pop(0)
            children = self.get_children(current_id)
            for child in children:
                if child.id not in descendants:
                    descendants.add(child.id)
                    queue.append(child.id)
        return descendants

    def get_with_tree(
        self,
        department_id: int,
        depth: int,
        include_employees: bool,
    ) -> Department | None:
        options = [selectinload(Department.children)]
        if include_employees:
            options.append(selectinload(Department.employees))

        stmt = (
            select(Department).where(Department.id == department_id).options(*options)
        )
        department = self.db.scalar(stmt)
        if department is None:
            return None

        if depth > 1:
            self._load_children_recursive(department, depth - 1, include_employees)
        return department

    def _load_children_recursive(
        self,
        department: Department,
        remaining_depth: int,
        include_employees: bool,
    ) -> None:
        if remaining_depth <= 0:
            return

        child_ids = [child.id for child in department.children]
        if not child_ids:
            return

        options = [selectinload(Department.children)]
        if include_employees:
            options.append(selectinload(Department.employees))

        stmt = select(Department).where(Department.id.in_(child_ids)).options(*options)
        loaded_children = {child.id: child for child in self.db.scalars(stmt).all()}
        department.children = [
            loaded_children[child.id] for child in department.children
        ]

        if remaining_depth > 1:
            for child in department.children:
                self._load_children_recursive(
                    child, remaining_depth - 1, include_employees
                )

    def reassign_employees(
        self, from_department_id: int, to_department_id: int
    ) -> None:
        stmt = select(Employee).where(Employee.department_id == from_department_id)
        employees = self.db.scalars(stmt).all()
        for employee in employees:
            employee.department_id = to_department_id
        self.db.flush()

    def move_children_to_parent(
        self,
        department: Department,
        new_parent_id: int | None,
    ) -> None:
        for child in department.children:
            child.parent_id = new_parent_id
        self.db.flush()
