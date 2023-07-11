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
root.geometry("1250x750")

app_font = customtkinter.CTkFont("Montserrat", weight="bold", size=15)
task_font = customtkinter.CTkFont("Montserrat", weight="bold", size=15)
category_font = customtkinter.CTkFont("Montserrat", size=15)


task_list = []
task_notes = []
category_list = []
category_buttons = []
all_category = []


def get_tasks():
    task_list.clear()
    if all_category[0].get() == 1:
        cursor.execute("""SELECT * FROM public.tasks ORDER BY date_due ASC, time_due ASC""")
        tasks = cursor.fetchall()
        for task in tasks:
            task_list.append(task)
    else:
        categories_to_get = []
        for category in category_buttons:
            if category.get() != 0:
                categories_to_get.append(category.cget("onvalue"))

        cursor.execute("""SELECT * FROM tasks WHERE task_category = ANY(%s) ORDER BY date_due ASC, time_due ASC""", (categories_to_get,))
        tasks = cursor.fetchall()
        for task in tasks:
            task_list.append(task)

    print(task_list)


def draw_tasks():
    row_counter = 1
    for tasks in task_list:

        task_str = str(tasks["task_name"])
        task_label = customtkinter.CTkButton(master=right_frame, width=400, height=62, fg_color="#dbdbdb", text_color="black" ,border_color="black", border_width=1, font=app_font, text=task_str)
        task_label.grid(row=row_counter, column=0)

        notes = []

        if tasks["task_notes"] != None:
            tasks_notes_frame = customtkinter.CTkScrollableFrame(master=right_frame, width=340, label_fg_color="black")
            tasks_notes_frame.grid(row=row_counter, column=1, sticky="ew", pady=2)

            note_counter = 0
            for task_note in tasks["task_notes"]:
                task_note_checkbox = customtkinter.CTkCheckBox(master=tasks_notes_frame, font=app_font, text=task_note, width=340)
                task_note_checkbox.grid(row=note_counter, column=0, pady=10, padx=10)
                notes.append(task_note_checkbox)
                note_counter += 1
        else:
            tasks_notes_label = customtkinter.CTkLabel(master=right_frame, width=360, height=60, fg_color="#dbdbdb", corner_radius=5, text="")
            tasks_notes_label.grid(row=row_counter, column=1, pady=2)

        task_notes.append(notes)
        print(notes)
        row_counter += 1


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
            category_filter_checkbox = customtkinter.CTkCheckBox(master=left_frame, width=100, height=40,
                                                                 text_color="white", text=category_str,
                                                                 onvalue=str(category), command=deselect_all_filter)
            category_buttons.append(category_filter_checkbox)
            category_filter_checkbox.grid(row=row_counter, pady=5, column=0)

        else:
            all_filter_checkbox = customtkinter.CTkCheckBox(master=left_frame, width=100, height=40,
                                                            text_color="white", text=category_str,
                                                            command=deselect_filters)
            all_filter_checkbox.select()
            all_category.append(all_filter_checkbox)
            all_filter_checkbox.grid(row=row_counter, pady=10, column=0)

        row_counter += 1



def add_task():
    root.geometry("1200x750")


left_frame = customtkinter.CTkFrame(master=root, width=250, height=750, fg_color="#1f1e1c")
left_frame.place(x=0, y=0)

right_frame = customtkinter.CTkScrollableFrame(master=root, width=1000, height=750, fg_color="#232323", scrollbar_button_color="white")
right_frame.place(x=250, y=0)

left_title_label = customtkinter.CTkLabel(master=left_frame, justify="center", font=app_font, fg_color="#232323", width=248, height=62, pady=20, padx=1,text_color="white", text="Categories")
left_title_label.grid(row=0, column=0)

draw_categories()
get_tasks()

button_row = len(category_buttons) + 2
filter_button = customtkinter.CTkButton(master=left_frame, width=200, height=50, fg_color="#232323", text_color="white", text="Apply filters", command=get_tasks)
filter_button.grid(row=button_row, column=0)

to_do_title_label = customtkinter.CTkLabel(master=right_frame, justify="center", font=app_font, fg_color="#232323", width=400, height=62, pady=20, padx=1, text_color="white", text="To-Do List")
to_do_title_label.grid(row=0, column=0, rowspan=1)

notes_title_label = customtkinter.CTkLabel(master=right_frame, justify="center", font=app_font, fg_color="#232323", corner_radius=4, width=340, pady=20, text_color="white", text="Notes")
notes_title_label.grid(row=0, column=1)

edit_title_label = customtkinter.CTkLabel(master=right_frame, justify="center", font=app_font, fg_color="#232323", width=250, pady=20, text_color="white", text="Due")
edit_title_label.grid(row=0, column=2)

draw_tasks()


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


