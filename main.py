import time

from fastapi import FastAPI, status, HTTPException
from pydantic import BaseModel
from datetime import date, datetime

import psycopg
from psycopg.rows import dict_row


app = FastAPI()


class Task(BaseModel):
    task_name: str
    task_category: str = "Other"
    date_due: str = date.today()
    time_due: datetime = datetime.now().strftime("%H:%M:%S")
    finished: bool = False


while True:
    try:
        conn = psycopg.connect(host="localhost", dbname="To-Do-Planner", user="postgres", password="postgresPass1.", row_factory=dict_row)
        cursor = conn.cursor()
        print("Database connection successful")
        break
    except Exception as error:
        print("Connection to database failed!")
        print("Error: ", error)
        time.sleep(2)


@app.get("/")
def root():
    return {"message": "Welcome to my api!"}


@app.get("/tasks")
def get_tasks():
    cursor.execute("""SELECT * FROM tasks""")
    tasks = cursor.fetchall()
    return {"tasks": tasks}


@app.get("/tasks/{category}")
def get_tasks_with_category(category: str):
    cursor.execute("""SELECT * FROM tasks WHERE task_category = %s""", (category,))
    tasks = cursor.fetchall()
    if not tasks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"no tasks under category: {category}")
    return {"tasks": tasks}


@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(task: Task):
    cursor.execute("""INSERT INTO tasks (task_name, task_category, date_due, time_due, task_finished) VALUES (%s, %s, %s, %s, %s) RETURNING *""", (task.task_name, task.task_category, task.date_due, task.time_due, task.finished))
    new_task = cursor.fetchone()
    conn.commit()
    return {"task": new_task}


@app.delete("/tasks/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(id:int):
    cursor.execute("""DELETE FROM tasks WHERE id = %s RETURNING *""", (str(id),))
    deleted_task = cursor.fetchone()
    conn.commit()

    if not deleted_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"no tasks with id: {id} was not found")

