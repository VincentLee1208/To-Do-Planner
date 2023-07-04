import time

from fastapi import FastAPI, Response, status, HTTPException
from pydantic import BaseModel
from datetime import date

import psycopg
from psycopg.rows import dict_row


app = FastAPI()


class Task(BaseModel):
    task_name: str
    date_due: date
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
    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()
    return {"tasks": tasks}


@app.get("/tasks/{category}")
def get_tasks_with_category(category: str):
    cursor.execute("""SELECT * FROM tasks WHERE task_category = %s""", (category,))
    tasks = cursor.fetchall()
    if not tasks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"no tasks under category: {category}")
    return {"tasks": tasks}
