from typing import List

from sqlalchemy import create_engine, Integer, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Department(Base):
    __tablename__ = "department"

    id_dept: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dept_name: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[str] = mapped_column(String(100), nullable=False)

    employees: Mapped[List["Employee"]] = relationship(
        "Employee", back_populates="department"
    )


class Employee(Base):
    __tablename__ = "employee"

    id_emp: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_dept: Mapped[int] = mapped_column(ForeignKey("department.id_dept"), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[str] = mapped_column(String(100), nullable=False)

    department: Mapped["Department"] = relationship(
        "Department", back_populates="employees"
    )
    badges: Mapped[List["Badge"]] = relationship(
        "Badge", back_populates="employee"
    )
    project_participations: Mapped[List["EmployeeProject"]] = relationship(
        "EmployeeProject", back_populates="employee"
    )


class Badge(Base):
    __tablename__ = "badge"

    id_badge: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_emp: Mapped[int] = mapped_column(ForeignKey("employee.id_emp"), nullable=False)
    card_code: Mapped[str] = mapped_column(String(50), nullable=False)

    employee: Mapped["Employee"] = relationship(
        "Employee", back_populates="badges"
    )


class Project(Base):
    __tablename__ = "project"

    id_project: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    proj_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)

    employee_participations: Mapped[List["EmployeeProject"]] = relationship(
        "EmployeeProject", back_populates="project"
    )


class EmployeeProject(Base):
    __tablename__ = "employee_project"

    id_emp: Mapped[int] = mapped_column(
        ForeignKey("employee.id_emp"), primary_key=True
    )
    id_project: Mapped[int] = mapped_column(
        ForeignKey("project.id_project"), primary_key=True
    )
    role_in_proj: Mapped[str] = mapped_column(String(100), nullable=False)

    employee: Mapped["Employee"] = relationship(
        "Employee", back_populates="project_participations"
    )
    project: Mapped["Project"] = relationship(
        "Project", back_populates="employee_participations"
    )


if __name__ == "__main__":
    # Перед запуском создайте базу данных company_db в MySQL.
    DATABASE_URL = "mysql+pymysql://root:@127.0.0.1:3306/company_db"

    engine = create_engine(DATABASE_URL, echo=True)

    print("Создаем таблицы в базе данных")
    Base.metadata.create_all(engine)
    print("Все таблицы и связи успешно созданы")
