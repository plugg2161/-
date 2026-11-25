import mysql.connector
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional

DB_CONFIG = {
    "user": "root",
    "password": "",
    "host": "127.0.0.1",
    "database": "students",
}

app = FastAPI(
    title="Company Database CRUD API",
    description="CRUD API для отделов, сотрудников, пропусков и проектов",
    version="1.0.0",
)


def execute_query(query, params=(), fetch=None, commit=False):
    """Выполняет запрос и корректно закрывает соединение."""
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params)

        if commit:
            connection.commit()
            return {"lastrowid": cursor.lastrowid, "rowcount": cursor.rowcount}
        if fetch == "one":
            return cursor.fetchone()
        if fetch == "all":
            return cursor.fetchall()
        return None

    except mysql.connector.IntegrityError as err:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=409, detail=f"Нарушено ограничение БД: {err}")
    except mysql.connector.Error as err:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=400, detail=f"Ошибка MySQL: {err}")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def ensure_exists(table: str, id_column: str, value: int, label: str):
    # Имена таблиц/столбцов передаются только из фиксированных вызовов ниже.
    result = execute_query(
        f"SELECT `{id_column}` FROM `{table}` WHERE `{id_column}`=%s",
        (value,), fetch="one",
    )
    if result is None:
        raise HTTPException(status_code=404, detail=f"{label} не найдена/не найден")


# -------------------- Модели запросов --------------------

class DepartmentIn(BaseModel):
    dept_name: str = Field(..., min_length=1, max_length=255)
    location: str = Field(..., min_length=1, max_length=255)


class EmployeeIn(BaseModel):
    id_dept: int
    full_name: str = Field(..., min_length=1, max_length=255)
    position: str = Field(..., min_length=1, max_length=255)


class BadgeIn(BaseModel):
    id_emp: int
    card_code: str = Field(..., min_length=1, max_length=255)


class ProjectIn(BaseModel):
    proj_name: str = Field(..., min_length=1, max_length=255)
    status: str = Field(..., min_length=1, max_length=100)


class ProjectParticipationIn(BaseModel):
    id_emp: int
    id_project: int
    role_in_proj: str = Field(..., min_length=1, max_length=255)


# ==================== ОТДЕЛ ====================

@app.post("/departments/", status_code=status.HTTP_201_CREATED, tags=["Отдел"])
def create_department(item: DepartmentIn):
    result = execute_query(
        "INSERT INTO `Отдел` (dept_name, location) VALUES (%s, %s)",
        (item.dept_name, item.location), commit=True,
    )
    return {**item.model_dump(), "id_dept": result["lastrowid"]}


@app.get("/departments/", tags=["Отдел"])
def get_departments(limit: int = 100, offset: int = 0):
    if limit < 1 or limit > 1000 or offset < 0:
        raise HTTPException(status_code=400, detail="Некорректные limit или offset")
    return execute_query(
        "SELECT id_dept, dept_name, location FROM `Отдел` LIMIT %s OFFSET %s",
        (limit, offset), fetch="all",
    )


@app.get("/departments/{id_dept}", tags=["Отдел"])
def get_department(id_dept: int):
    result = execute_query(
        "SELECT id_dept, dept_name, location FROM `Отдел` WHERE id_dept=%s",
        (id_dept,), fetch="one",
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Отдел не найден")
    return result


@app.put("/departments/{id_dept}", tags=["Отдел"])
def update_department(id_dept: int, item: DepartmentIn):
    ensure_exists("Отдел", "id_dept", id_dept, "Отдел")
    execute_query(
        "UPDATE `Отдел` SET dept_name=%s, location=%s WHERE id_dept=%s",
        (item.dept_name, item.location, id_dept), commit=True,
    )
    return {**item.model_dump(), "id_dept": id_dept}


@app.delete("/departments/{id_dept}", status_code=status.HTTP_204_NO_CONTENT, tags=["Отдел"])
def delete_department(id_dept: int):
    ensure_exists("Отдел", "id_dept", id_dept, "Отдел")
    execute_query("DELETE FROM `Отдел` WHERE id_dept=%s", (id_dept,), commit=True)
    return None


# ==================== СОТРУДНИК ====================

@app.post("/employees/", status_code=status.HTTP_201_CREATED, tags=["Сотрудник"])
def create_employee(item: EmployeeIn):
    result = execute_query(
        "INSERT INTO `Сотрудник` (id_dept, full_name, position) VALUES (%s, %s, %s)",
        (item.id_dept, item.full_name, item.position), commit=True,
    )
    return {**item.model_dump(), "id_emp": result["lastrowid"]}


@app.get("/employees/", tags=["Сотрудник"])
def get_employees(limit: int = 100, offset: int = 0):
    if limit < 1 or limit > 1000 or offset < 0:
        raise HTTPException(status_code=400, detail="Некорректные limit или offset")
    return execute_query(
        "SELECT id_emp, id_dept, full_name, position FROM `Сотрудник` LIMIT %s OFFSET %s",
        (limit, offset), fetch="all",
    )


@app.get("/employees/{id_emp}", tags=["Сотрудник"])
def get_employee(id_emp: int):
    result = execute_query(
        "SELECT id_emp, id_dept, full_name, position FROM `Сотрудник` WHERE id_emp=%s",
        (id_emp,), fetch="one",
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")
    return result


@app.put("/employees/{id_emp}", tags=["Сотрудник"])
def update_employee(id_emp: int, item: EmployeeIn):
    ensure_exists("Сотрудник", "id_emp", id_emp, "Сотрудник")
    execute_query(
        "UPDATE `Сотрудник` SET id_dept=%s, full_name=%s, position=%s WHERE id_emp=%s",
        (item.id_dept, item.full_name, item.position, id_emp), commit=True,
    )
    return {**item.model_dump(), "id_emp": id_emp}


@app.delete("/employees/{id_emp}", status_code=status.HTTP_204_NO_CONTENT, tags=["Сотрудник"])
def delete_employee(id_emp: int):
    ensure_exists("Сотрудник", "id_emp", id_emp, "Сотрудник")
    execute_query("DELETE FROM `Сотрудник` WHERE id_emp=%s", (id_emp,), commit=True)
    return None


# ==================== ПРОПУСК ====================

@app.post("/badges/", status_code=status.HTTP_201_CREATED, tags=["Пропуск"])
def create_badge(item: BadgeIn):
    result = execute_query(
        "INSERT INTO `Пропуск` (id_emp, card_code) VALUES (%s, %s)",
        (item.id_emp, item.card_code), commit=True,
    )
    return {**item.model_dump(), "id_badge": result["lastrowid"]}


@app.get("/badges/", tags=["Пропуск"])
def get_badges(limit: int = 100, offset: int = 0):
    if limit < 1 or limit > 1000 or offset < 0:
        raise HTTPException(status_code=400, detail="Некорректные limit или offset")
    return execute_query(
        "SELECT id_badge, id_emp, card_code FROM `Пропуск` LIMIT %s OFFSET %s",
        (limit, offset), fetch="all",
    )


@app.get("/badges/{id_badge}", tags=["Пропуск"])
def get_badge(id_badge: int):
    result = execute_query(
        "SELECT id_badge, id_emp, card_code FROM `Пропуск` WHERE id_badge=%s",
        (id_badge,), fetch="one",
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Пропуск не найден")
    return result


@app.put("/badges/{id_badge}", tags=["Пропуск"])
def update_badge(id_badge: int, item: BadgeIn):
    ensure_exists("Пропуск", "id_badge", id_badge, "Пропуск")
    execute_query(
        "UPDATE `Пропуск` SET id_emp=%s, card_code=%s WHERE id_badge=%s",
        (item.id_emp, item.card_code, id_badge), commit=True,
    )
    return {**item.model_dump(), "id_badge": id_badge}


@app.delete("/badges/{id_badge}", status_code=status.HTTP_204_NO_CONTENT, tags=["Пропуск"])
def delete_badge(id_badge: int):
    ensure_exists("Пропуск", "id_badge", id_badge, "Пропуск")
    execute_query("DELETE FROM `Пропуск` WHERE id_badge=%s", (id_badge,), commit=True)
    return None


# ==================== ПРОЕКТ ====================

@app.post("/projects/", status_code=status.HTTP_201_CREATED, tags=["Проект"])
def create_project(item: ProjectIn):
    result = execute_query(
        "INSERT INTO `Проект` (proj_name, status) VALUES (%s, %s)",
        (item.proj_name, item.status), commit=True,
    )
    return {**item.model_dump(), "id_project": result["lastrowid"]}


@app.get("/projects/", tags=["Проект"])
def get_projects(limit: int = 100, offset: int = 0):
    if limit < 1 or limit > 1000 or offset < 0:
        raise HTTPException(status_code=400, detail="Некорректные limit или offset")
    return execute_query(
        "SELECT id_project, proj_name, status FROM `Проект` LIMIT %s OFFSET %s",
        (limit, offset), fetch="all",
    )


@app.get("/projects/{id_project}", tags=["Проект"])
def get_project(id_project: int):
    result = execute_query(
        "SELECT id_project, proj_name, status FROM `Проект` WHERE id_project=%s",
        (id_project,), fetch="one",
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Проект не найден")
    return result


@app.put("/projects/{id_project}", tags=["Проект"])
def update_project(id_project: int, item: ProjectIn):
    ensure_exists("Проект", "id_project", id_project, "Проект")
    execute_query(
        "UPDATE `Проект` SET proj_name=%s, status=%s WHERE id_project=%s",
        (item.proj_name, item.status, id_project), commit=True,
    )
    return {**item.model_dump(), "id_project": id_project}


@app.delete("/projects/{id_project}", status_code=status.HTTP_204_NO_CONTENT, tags=["Проект"])
def delete_project(id_project: int):
    ensure_exists("Проект", "id_project", id_project, "Проект")
    execute_query("DELETE FROM `Проект` WHERE id_project=%s", (id_project,), commit=True)
    return None


# ==================== УЧАСТИЕ В ПРОЕКТЕ ====================
# Предполагается составной первичный ключ: (id_emp, id_project).

@app.post("/project-participations/", status_code=status.HTTP_201_CREATED, tags=["Участие в проекте"])
def create_participation(item: ProjectParticipationIn):
    execute_query(
        "INSERT INTO `Участие в проекте` (id_emp, id_project, role_in_proj) VALUES (%s, %s, %s)",
        (item.id_emp, item.id_project, item.role_in_proj), commit=True,
    )
    return item.model_dump()


@app.get("/project-participations/", tags=["Участие в проекте"])
def get_participations(limit: int = 100, offset: int = 0):
    if limit < 1 or limit > 1000 or offset < 0:
        raise HTTPException(status_code=400, detail="Некорректные limit или offset")
    return execute_query(
        "SELECT id_emp, id_project, role_in_proj FROM `Участие в проекте` LIMIT %s OFFSET %s",
        (limit, offset), fetch="all",
    )


@app.get("/project-participations/{id_emp}/{id_project}", tags=["Участие в проекте"])
def get_participation(id_emp: int, id_project: int):
    result = execute_query(
        "SELECT id_emp, id_project, role_in_proj FROM `Участие в проекте` "
        "WHERE id_emp=%s AND id_project=%s",
        (id_emp, id_project), fetch="one",
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Участие в проекте не найдено")
    return result


@app.put("/project-participations/{id_emp}/{id_project}", tags=["Участие в проекте"])
def update_participation(id_emp: int, id_project: int, item: ProjectParticipationIn):
    exists = execute_query(
        "SELECT id_emp FROM `Участие в проекте` WHERE id_emp=%s AND id_project=%s",
        (id_emp, id_project), fetch="one",
    )
    if exists is None:
        raise HTTPException(status_code=404, detail="Участие в проекте не найдено")
    if item.id_emp != id_emp or item.id_project != id_project:
        raise HTTPException(status_code=400, detail="id_emp и id_project в теле должны совпадать с URL")
    execute_query(
        "UPDATE `Участие в проекте` SET role_in_proj=%s WHERE id_emp=%s AND id_project=%s",
        (item.role_in_proj, id_emp, id_project), commit=True,
    )
    return item.model_dump()


@app.delete("/project-participations/{id_emp}/{id_project}",
            status_code=status.HTTP_204_NO_CONTENT, tags=["Участие в проекте"])
def delete_participation(id_emp: int, id_project: int):
    exists = execute_query(
        "SELECT id_emp FROM `Участие в проекте` WHERE id_emp=%s AND id_project=%s",
        (id_emp, id_project), fetch="one",
    )
    if exists is None:
        raise HTTPException(status_code=404, detail="Участие в проекте не найдено")
    execute_query(
        "DELETE FROM `Участие в проекте` WHERE id_emp=%s AND id_project=%s",
        (id_emp, id_project), commit=True,
    )
    return None


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("CRUD_company:app", host="127.0.0.1", port=8000, reload=True)
