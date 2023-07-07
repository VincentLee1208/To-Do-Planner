import json

from pydantic import BaseModel
from datetime import date, datetime

import psycopg
import time
import customtkinter
from psycopg.rows import dict_row



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


root = customtkinter.CTk(fg_color="#1f1e1c")
root.minsize(width=750, height=750)
root.resizable(height=False, width=False)
root.geometry("1000x750")

app_font = customtkinter.CTkFont("Montserrat", weight="bold", size=15)
category_font = customtkinter.CTkFont("Montserrat", size=15)


task_list = []
category_list = []
category_buttons = []
all_category = []


def get_tasks():
    task_list.clear()
    if all_category[0].get() == 1:
        cursor.execute("""SELECT * FROM tasks""")
        tasks = cursor.fetchall()
        for task in tasks:
            task_list.append(task)
    else:
        for category in category_buttons:
            if category.get() != 0:
                print(category.cget("onvalue"))
                cursor.execute("""SELECT * FROM tasks WHERE task_category = %s""", (category.cget("onvalue"),))
                tasks = cursor.fetchall()
                for task in tasks:
                    task_list.append(task)

    print(task_list)


def deselect_filters():
    for buttons in category_buttons:
        buttons.deselect()


def deselect_all_filter():
    all_category[0].deselect()


def draw_categories():
    cursor.execute("""SELECT DISTINCT task_category FROM tasks""")
    categories = cursor.fetchall()
    category_list.clear()
    all_category.clear()
    for category in categories:
        category_list.append(category["task_category"])

    category_list.append("All")

    row_counter = 1
    for category in category_list:
        category_str = str(category)
        if len(category_str) > 7:
            category_str = category_str[:7]
            category_str += "..."

        if category != "All":
            category_filter_checkbox = customtkinter.CTkCheckBox(master=left_content_frame, width=150, height=50, text_color="white", text=category_str, onvalue=str(category), command=deselect_all_filter)
            category_buttons.append(category_filter_checkbox)
            category_filter_checkbox.grid(row=row_counter, pady=10, column=0)

        else:
            all_filter_checkbox = customtkinter.CTkCheckBox(master=left_content_frame, width=150, height=50, text_color="white", text=category_str, command=deselect_filters)
            all_filter_checkbox.select()
            all_category.append(all_filter_checkbox)
            all_filter_checkbox.grid(row=row_counter, pady=10, column=0)

        row_counter += 1


def add_task():
    root.geometry("1000x750")


left_frame = customtkinter.CTkFrame(master=root, width=250, height=750, fg_color="#232323", border_width=0).place(x=0,y=0)
right_frame = customtkinter.CTkFrame(master=root, width=500, height=750, fg_color="#1f1e1c").place(x=250,y=0)


left_title_frame = customtkinter.CTkFrame(master=left_frame, width=250, height=62, fg_color="#232323", border_width=1, border_color="grey").place(x=0,y=0)

left_title_label = customtkinter.CTkLabel(master=left_title_frame, justify="center", font=app_font,fg_color="#232323", width=250, pady=20, text_color="white",text="Categories").grid(row=0, column=0)

left_content_frame = customtkinter.CTkFrame(master=left_frame, width=250, height=688, fg_color="#1f1e1c", border_width=2).place(x=0, y=63)

draw_categories()
get_tasks()

button_row = len(category_buttons) + 2
filter_button = customtkinter.CTkButton(master=left_content_frame, width=200, height=50, fg_color="#232323", text_color="white", text="Apply filters", command=get_tasks).grid(row=button_row, column=0)


root.mainloop()


#
# @app.get("/tasks/{category}")
# def get_tasks_with_category(category: str):
#     cursor.execute("""SELECT * FROM tasks WHERE task_category = %s""", (category,))
#     tasks = cursor.fetchall()
#     if not tasks:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"no tasks under category: {category}")
#     return {"tasks": tasks}
#
#
# @app.post("/tasks", status_code=status.HTTP_201_CREATED)
# def create_task(task: Task):
#     cursor.execute("""INSERT INTO tasks (task_name, task_category, date_due, time_due, task_finished) VALUES (%s, %s, %s, %s, %s) RETURNING *""", (task.task_name, task.task_category, task.date_due, task.time_due, task.finished))
#     new_task = cursor.fetchone()
#     conn.commit()
#     return {"task": new_task}
#
#
# @app.delete("/tasks/{id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_task(id:int):
#     cursor.execute("""DELETE FROM tasks WHERE id = %s RETURNING *""", (str(id),))
#     deleted_task = cursor.fetchone()
#     conn.commit()
#
#     if not deleted_task:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"no tasks with id: {id} was not found")


