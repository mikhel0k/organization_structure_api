from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.repositories.base import BaseRepository


class EmployeeRepository(BaseRepository[Employee]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Employee)

    def create(
        self,
        department_id: int,
        full_name: str,
        position: str,
        hired_at,
    ) -> Employee:
        return self.add(
            Employee(
                department_id=department_id,
                full_name=full_name,
                position=position,
                hired_at=hired_at,
            )
        )
