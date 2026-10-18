from sqlalchemy import event

from app.services import task_service


def test_list_tasks_does_not_cause_n_plus_one(db_session):
    for i in range(5):
        task_service.create_task(db_session, f"할 일 {i}", [f"태그{i}", "공통"])
    # 생성 시 세션에 남은 로딩 상태를 비워서 실제 조회 쿼리를 센다.
    db_session.expire_all()

    selects: list[str] = []

    def count_select(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            selects.append(statement)

    engine = db_session.get_bind()
    event.listen(engine, "before_cursor_execute", count_select)
    try:
        tasks = task_service.list_tasks(db_session)
        for task in tasks:
            _ = [tag.name for tag in task.tags]
    finally:
        event.remove(engine, "before_cursor_execute", count_select)

    assert len(tasks) == 5
    # 할 일 조회 1회 + 태그 조회 1회
    assert len(selects) == 2
