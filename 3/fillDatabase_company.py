import random
import mysql.connector
from faker import Faker

# Настройки подключения к MySQL
DB_CONFIG = {
    "user": "root",
    "password": "",
    "host": "127.0.0.1",
    "database": "students",  # замени, если база данных называется иначе
}

fake = Faker("ru_RU")

# Синтетические значения для справочников
DEPARTMENTS = [
    ("Отдел разработки", "Москва"),
    ("Отдел информационной безопасности", "Санкт-Петербург"),
    ("Отдел аналитики", "Казань"),
    ("Отдел технической поддержки", "Новосибирск"),
    ("Отдел управления проектами", "Екатеринбург"),
]

POSITIONS = [
    "Разработчик", "Системный аналитик", "Тестировщик",
    "Системный администратор", "Руководитель проекта",
    "Специалист технической поддержки", "Инженер по безопасности",
]

PROJECTS = [
    ("Корпоративный портал", "В работе"),
    ("Мобильное приложение", "Планируется"),
    ("Модернизация инфраструктуры", "В работе"),
    ("Система аналитики", "Завершён"),
    ("Защита информационной системы", "В работе"),
]

try:
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()
    print("Подключение к базе данных установлено.")

    # Очистка таблиц в порядке, учитывающем внешние ключи.
    # ВНИМАНИЕ: этот блок удаляет все существующие записи!
    print("Очистка таблиц...")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("TRUNCATE TABLE `Участие в проекте`")
    cursor.execute("TRUNCATE TABLE `Пропуск`")
    cursor.execute("TRUNCATE TABLE `Сотрудник`")
    cursor.execute("TRUNCATE TABLE `Проект`")
    cursor.execute("TRUNCATE TABLE `Отдел`")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

    # 1. Отдел: 5 записей
    cursor.executemany(
        "INSERT INTO `Отдел` (dept_name, location) VALUES (%s, %s)",
        DEPARTMENTS,
    )
    cursor.execute("SELECT id_dept FROM `Отдел`")
    department_ids = [row[0] for row in cursor.fetchall()]

    # 2. Проект: 5 записей
    cursor.executemany(
        "INSERT INTO `Проект` (proj_name, status) VALUES (%s, %s)",
        PROJECTS,
    )
    cursor.execute("SELECT id_project FROM `Проект`")
    project_ids = [row[0] for row in cursor.fetchall()]

    # 3. Сотрудник: 100 сотрудников
    employees = []
    for _ in range(100):
        employees.append((
            random.choice(department_ids),
            fake.name(),
            random.choice(POSITIONS),
        ))

    cursor.executemany(
        "INSERT INTO `Сотрудник` (id_dept, full_name, position) VALUES (%s, %s, %s)",
        employees,
    )
    cursor.execute("SELECT id_emp FROM `Сотрудник`")
    employee_ids = [row[0] for row in cursor.fetchall()]

    # 4. Пропуск: по одному пропуску на каждого сотрудника
    badges = []
    for employee_id in employee_ids:
        badges.append((employee_id, f"BADGE-{fake.unique.bothify(text='??####??').upper()}"))

    cursor.executemany(
        "INSERT INTO `Пропуск` (id_emp, card_code) VALUES (%s, %s)",
        badges,
    )

    # 5. Участие в проекте: от 1 до 3 проектов для каждого сотрудника.
    # Предполагается составной первичный ключ (id_emp, id_project).
    participation = []
    roles = ["Руководитель", "Разработчик", "Аналитик", "Тестировщик", "Консультант"]
    for employee_id in employee_ids:
        selected_projects = random.sample(project_ids, k=random.randint(1, min(3, len(project_ids))))
        for project_id in selected_projects:
            participation.append((
                employee_id,
                project_id,
                random.choice(roles),
            ))

    cursor.executemany(
        "INSERT INTO `Участие в проекте` (id_emp, id_project, role_in_proj) VALUES (%s, %s, %s)",
        participation,
    )

    connection.commit()
    print("База данных успешно заполнена синтетическими данными.")
    print(f"Отделов: {len(DEPARTMENTS)}")
    print(f"Проектов: {len(PROJECTS)}")
    print(f"Сотрудников: {len(employees)}")
    print(f"Пропусков: {len(badges)}")
    print(f"Записей об участии в проектах: {len(participation)}")

except mysql.connector.Error as err:
    print(f"Ошибка MySQL: {err}")
    if "connection" in locals() and connection.is_connected():
        connection.rollback()

finally:
    if "cursor" in locals():
        cursor.close()
    if "connection" in locals() and connection.is_connected():
        connection.close()
        print("Соединение с базой данных закрыто.")
