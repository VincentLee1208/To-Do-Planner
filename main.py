from pydantic import BaseModel
from datetime import date, datetime
from tkcalendar import Calendar
from tktimepicker import SpinTimePickerModern
from tktimepicker import constants
from dotenv import load_dotenv


import psycopg
import time
import customtkinter
import tkinter
import os
from psycopg.rows import dict_row


class Task(BaseModel):
    task_name: str
    task_category: str = "Other"
    date_due: str = date.today()
    time_due: datetime = datetime.now().strftime("%H:%M:%S")
    finished: bool = False


load_dotenv('./.env')

while True:
    try:
        conn = psycopg.connect(host="to-do-planner.cbhseyowwdhe.us-west-2.rds.amazonaws.com",
                               dbname="To_Do_Planner",
                               user="postgres",
                               password=os.environ.get("DATABASE_PASSWORD"),
                               port="5432",
                               row_factory=dict_row)
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
root.geometry("1300x750")

app_font = customtkinter.CTkFont("Montserrat", weight="bold", size=15)
task_font = customtkinter.CTkFont("Montserrat", weight="bold", size=18)
category_font = customtkinter.CTkFont("Montserrat", size=15)
exit_font = customtkinter.CTkFont("Asap", weight="bold", size=15)

task_list = []
task_notes = []
category_list = []
category_buttons = []
all_category = []
new_note_list = []

add_task_window = None
edit_image = tkinter.PhotoImage(file="./images/edit (1).png")
checked_image = tkinter.PhotoImage(file="./images/tick.png")
delete_image = tkinter.PhotoImage(file="./images/trash.png")

global time_selected
time_selected = False
global new_note_counter
new_note_counter = 1
global due_date
due_date = datetime.today().strftime('%Y-%m-%d')


def create_table():
    cursor.execute("""CREATE TABLE IF NOT EXISTS tasks (
                        id SERIAL PRIMARY KEY NOT NULL,
                        task_name VARCHAR NOT NULL,
                        task_category VARCHAR DEFAULT 'Other',
                        date_due DATE NOT NULL,
                        time_due TIME,
                        task_finished BOOLEAN NOT NULL DEFAULT false,
                        task_priority INTEGER NOT NULL DEFAULT 1,
                        task_notes VARCHAR[]
    )""")
    conn.commit()


def get_tasks():
    task_list.clear()
    if all_category[0].get() == 1:
        cursor.execute("""SELECT * FROM tasks ORDER BY 
                          CASE 
                            WHEN task_finished = 'false' THEN 0
                            WHEN task_finished = 'true' THEN 1
                          END,
                          date_due ASC,
                          time_due ASC;""")
    else:
        categories_to_get = []
        for category in category_buttons:
            if category.get() != 0:
                categories_to_get.append(category.cget("onvalue"))

        cursor.execute("""SELECT * FROM tasks WHERE task_category = ANY(%s) ORDER BY 
                          CASE 
                            WHEN task_finished = 'false' THEN 0
                            WHEN task_finished = 'true' THEN 1
                          END,
                          date_due ASC,
                          time_due ASC;""",
                       (categories_to_get,))

    tasks = cursor.fetchall()
    for task in tasks:
        task_list.append(task)


def submit_task(task_name, task_category, time_picker, task_priority_box, notes_frame, submit_task_frame, task_option,
                task_id=None):
    if task_name.get() == "":
        window = customtkinter.CTkToplevel(fg_color="#232323")
        window.geometry("%dx%d+%d+%d" % (300, 90, 2000, 300))
        window.transient(master=notes_frame)
        window.resizable(False, False)

        error_label = customtkinter.CTkLabel(master=window, width=300, height=30, font=app_font, fg_color="#232323",
                                             justify="center", text_color="white", text="Task Name cannot be empty")
        error_label.grid(row=0, column=0, pady=5)

        okay_button = customtkinter.CTkButton(master=window, width=100, height=30, font=app_font, fg_color="#dbdbdb",
                                              text_color="black", text="Okay", command=lambda: destroy_window(window))
        okay_button.grid(row=1, column=0, pady=10)

    else:
        global time_selected
        global due_date
        task_name_str = task_name.get()
        task_category_str = "Other"
        due_date_str = str(due_date)
        time_due_str = None
        task_priority_str = task_priority_box.get()
        notes = []

        window = customtkinter.CTkToplevel(fg_color="#232323")
        window.geometry("%dx%d+%d+%d" % (300, 90, 2000, 300))
        window.transient(master=notes_frame)
        window.resizable(False, False)

        if time_selected is True:
            time_due = time_picker.time()
            time_due_str = ""
            hour = time_due[0]
            minutes = time_due[1]

            if time_due[2] == "PM":
                hour += 12
                if hour == 24:
                    hour = 0

            time_due_str += str(hour)
            time_due_str += ":"
            time_due_str += str(minutes)

        if len(new_note_list) == 0:
            notes = None
        else:
            for new_notes in new_note_list:
                notes.append(new_notes.get())

        if task_category.get() != "":
            task_category_str = task_category.get()

        if task_option == "Add":
            cursor.execute(
                """INSERT INTO tasks (task_name, task_category, date_due, time_due, task_finished, task_priority, task_notes) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING *""",
                (task_name_str, task_category_str, due_date_str, time_due_str, False, task_priority_str, notes))

            conn.commit()

            success_label = customtkinter.CTkLabel(master=window, width=300, height=30, font=app_font,
                                                   fg_color="#232323",
                                                   justify="center", text_color="white",
                                                   text="Task added successfully!")
            success_label.grid(row=0, column=0, pady=5)

            destroy_add_task(submit_task_frame)
        elif task_option == "Update":
            cursor.execute("""UPDATE tasks 
                                SET task_name = %s, 
                                    task_category= %s, 
                                    date_due= %s, 
                                    time_due = %s, 
                                    task_finished = %s, 
                                    task_priority = %s, 
                                    task_notes = %s 
                                WHERE id = %s""",
                           (task_name_str, task_category_str, due_date_str, time_due_str, False, task_priority_str,
                            notes, task_id))
            conn.commit()

            success_label = customtkinter.CTkLabel(master=window, width=300, height=30, font=app_font,
                                                   fg_color="#232323",
                                                   justify="center", text_color="white",
                                                   text="Task updated successfully!")
            success_label.grid(row=0, column=0, pady=5)

            destroy_window(submit_task_frame)

        okay_button = customtkinter.CTkButton(master=window, width=100, height=30, font=app_font, fg_color="#dbdbdb",
                                              text_color="black", text="Okay", command=lambda: destroy_window(window))
        okay_button.grid(row=1, column=0, pady=10)

        # clear all data
        new_note_list.clear()
        time_selected = False
        due_date = datetime.today().strftime('%Y-%m-%d')

        redraw_categories()
        redraw_tasks()


def delete_task(task, notes=None):
    if notes is not None:
        for note in notes:
            if note.get() == 0:
                check_window = customtkinter.CTkToplevel()
                check_window.geometry("300x100")
                check_window.transient(master=root)
                check_window_frame = customtkinter.CTkFrame(master=check_window, fg_color="#1f1e1c")
                check_window_frame.place(x=0, y=0)

                check_window_label = customtkinter.CTkLabel(master=check_window_frame, width=300, height=40,
                                                            font=app_font, text_color="white",
                                                            text="Not all notes have been completed! \n Are you sure you want to delete task?")
                check_window_label.grid(row=0, column=0, columnspan=2, pady=5)

                yes_button = customtkinter.CTkButton(master=check_window_frame, width=50, height=30, font=app_font,
                                                     text_color="white", text="Yes",
                                                     command=lambda: remove_task(task, check_window))
                yes_button.grid(row=1, column=0, padx=10, pady=10)

                no_button = customtkinter.CTkButton(master=check_window_frame, width=50, height=30, font=app_font,
                                                    text_color="white", text="No",
                                                    command=lambda: destroy_window(check_window))
                no_button.grid(row=1, column=1, padx=10, pady=10)

                return

    remove_task(task)


def remove_task(task, check_window=None):
    if check_window is not None:
        destroy_window(check_window)

    task_id = task["id"]
    cursor.execute("""DELETE FROM tasks WHERE id = %s RETURNING *""", (str(task_id),))
    conn.commit()

    success_window = customtkinter.CTkToplevel()
    success_window.geometry("300x100")
    success_window.transient(master=root)

    success_window.transient(master=root)
    success_window_frame = customtkinter.CTkFrame(master=success_window, fg_color="#1f1e1c")
    success_window_frame.place(x=0, y=0)

    success_window_label = customtkinter.CTkLabel(master=success_window_frame, width=300, height=40, font=app_font,
                                                  text_color="white",
                                                  text="Task has been successfully deleted!")
    success_window_label.grid(row=0, column=0, pady=5)

    okay_button = customtkinter.CTkButton(master=success_window_frame, width=50, height=30, font=app_font,
                                          text_color="white", text="Okay",
                                          command=lambda: destroy_window(success_window))
    okay_button.grid(row=1, column=0, pady=10)

    redraw_tasks()
    redraw_categories()


def complete_task(task, notes=None):
    if not task["task_finished"]:
        if notes is not None:
            for note in notes:
                if note.get() == 0:
                    check_window = customtkinter.CTkToplevel()
                    check_window.geometry("300x100")
                    check_window.transient(master=root)
                    check_window_frame = customtkinter.CTkFrame(master=check_window, fg_color="#1f1e1c")
                    check_window_frame.place(x=0, y=0)

                    check_window_label = customtkinter.CTkLabel(master=check_window_frame, width=300, height=40,
                                                                font=app_font, text_color="white",
                                                                text="Not all notes have been completed! \n Are you sure you want to complete task?")
                    check_window_label.grid(row=0, column=0, columnspan=2, pady=5)

                    yes_button = customtkinter.CTkButton(master=check_window_frame, width=50, height=30, font=app_font,
                                                         text_color="white", text="Yes",
                                                         command=lambda: change_task_complete(task, check_window))
                    yes_button.grid(row=1, column=0, padx=10, pady=10)

                    no_button = customtkinter.CTkButton(master=check_window_frame, width=50, height=30, font=app_font,
                                                        text_color="white", text="No",
                                                        command=lambda: destroy_window(check_window))
                    no_button.grid(row=1, column=1, padx=10, pady=10)

                    return

        change_task_complete(task)
    else:
        change_task_complete(task)


def change_task_complete(task, check_window=None):
    if check_window is not None:
        destroy_window(check_window)

    task_id = task["id"]
    if task["task_finished"] is False:
        cursor.execute("""UPDATE tasks SET task_finished = true WHERE id = %s""", (str(task_id),))
        conn.commit()
    else:
        cursor.execute("""UPDATE tasks SET task_finished = false WHERE id = %s""", (str(task_id),))
        conn.commit()

    redraw_tasks()
    redraw_categories()


def create_edit_window(task):
    edit_window = customtkinter.CTkToplevel()
    edit_window.geometry("430x750")
    edit_window.transient(master=root)
    edit_window.resizable(False, False)

    edit_task_frame = customtkinter.CTkScrollableFrame(master=edit_window, width=420, height=750, fg_color="#232323")
    edit_task_frame.grid(row=0, column=0)

    edit_label = customtkinter.CTkLabel(master=edit_task_frame, width=330, height=62, font=task_font,
                                        text_color="white", text="Edit Task", anchor="w")
    edit_label.grid(row=0, column=0, padx=(10, 0))

    close_button = customtkinter.CTkButton(master=edit_task_frame, width=40, fg_color="#232323", font=exit_font,
                                           text_color="white", text="X", command=lambda: destroy_window(edit_window))
    close_button.grid(row=0, column=1, padx=10)

    task_name_label = customtkinter.CTkLabel(master=edit_task_frame, width=400, height=30, font=app_font,
                                             text_color="white", text="Task Name: ", anchor="w")
    task_name_label.grid(row=1, column=0, columnspan=2, padx=10)

    task_name_stringvar = customtkinter.StringVar(value=task["task_name"])
    task_name = customtkinter.CTkEntry(master=edit_task_frame, width=400, height=30, font=app_font,
                                       textvariable=task_name_stringvar)
    task_name.grid(row=2, column=0, columnspan=2, pady=5, padx=10)

    task_category_label = customtkinter.CTkLabel(master=edit_task_frame, width=400, height=30, font=app_font,
                                                 text_color="white", text="Task Category: ", anchor="w")
    task_category_label.grid(row=3, column=0, columnspan=2, padx=10)

    task_category_stringvar = customtkinter.StringVar(value=task["task_category"])
    task_category = customtkinter.CTkEntry(master=edit_task_frame, width=400, height=30, font=app_font,
                                           textvariable=task_category_stringvar)
    task_category.grid(row=4, column=0, columnspan=2, pady=5, padx=10)

    due_date_frame = customtkinter.CTkFrame(master=edit_task_frame, width=400, height=40, fg_color="#232323",
                                            corner_radius=5)
    due_date_frame.grid(row=5, column=0, columnspan=2, pady=5)

    due_label = customtkinter.CTkLabel(master=due_date_frame, text="Due: ", font=app_font, text_color="white", width=50,
                                       height=40, fg_color="#232323")
    due_label.grid(row=0, column=0, pady=5)

    global due_date
    due_date = task["date_due"]

    task_date_due = customtkinter.CTkButton(master=due_date_frame, text=task["date_due"], text_color="white",
                                            fg_color="#1f1e1c", width=300, height=40, font=app_font,
                                            command=lambda: open_calendar(due_date_frame, task_date_due))
    task_date_due.grid(row=0, column=1, pady=5)

    time_picker_frame = customtkinter.CTkFrame(master=edit_task_frame, width=350, height=40, fg_color="#232323")

    time_picker = SpinTimePickerModern(time_picker_frame)
    time_picker.addAll(constants.HOURS12)
    time_picker.configureAll(bg="#404040", height=1, fg="#dbdbdb", font=app_font, hoverbg="#dbdbdb",
                             hovercolor="#2dbbd0", clickedbg="#dbdbdb", clickedcolor="#2dbbd0")
    time_picker.configure_separator(bg="#404040", fg="#ffffff")

    time_picker_button = customtkinter.CTkButton(master=edit_task_frame, width=300, height=30, fg_color="#dbdbdb",
                                                 text_color="black", font=app_font, text="Set Optional Time Deadline",
                                                 command=lambda:
                                                 add_time_picker(time_picker_frame, time_picker, 6, time_picker_button))

    if task["time_due"] is not None:
        if task["time_due"].hour >= 13:
            time_picker.set12Hrs(task["time_due"].hour - 12)
        else:
            time_picker.set12Hrs(task["time_due"].hour)

        time_picker.setMins(task["time_due"].minute)
        add_time_picker(time_picker_frame, time_picker, 6, time_picker_button)

    task_priority_frame = customtkinter.CTkFrame(master=edit_task_frame, width=400, height=30, fg_color="#232323")
    task_priority_frame.grid(row=7, column=0, columnspan=2, pady=10)

    task_priority_label = customtkinter.CTkLabel(master=task_priority_frame, width=30, font=app_font,
                                                 text_color="white", text="Task Priority: ")
    task_priority_label.grid(row=0, column=0, padx=10)

    task_priority_box = customtkinter.CTkComboBox(master=task_priority_frame, fg_color="#1f1e1c",
                                                  values=["1", "2", "3", "4", "5"], font=app_font, text_color="white")
    task_priority_box.set(str(task["task_priority"]))
    task_priority_box.grid(row=0, column=1)

    notes_frame = customtkinter.CTkFrame(master=edit_task_frame, width=350, fg_color="#232323")

    if task["task_notes"] is None:
        notes_to_display = []
        add_notes_button = customtkinter.CTkButton(master=edit_task_frame, width=300, height=30, fg_color="#dbdbdb",
                                                   text_color="black", font=app_font, text="Add Notes",
                                                   command=lambda: add_note_section(edit_task_frame, notes_frame,
                                                                                    add_notes_button, 8,
                                                                                    notes_to_display))
        add_notes_button.grid(row=8, column=0, columnspan=2, pady=5)
    else:
        notes_to_display = task["task_notes"]
        add_notes_button = customtkinter.CTkButton(master=edit_task_frame, width=300, height=30, fg_color="#dbdbdb",
                                                   text_color="black", font=app_font, text="Add Notes",
                                                   command=lambda: add_note_section(edit_task_frame, notes_frame,
                                                                                    add_notes_button, 8,
                                                                                    notes_to_display))
        add_note_section(edit_task_frame, notes_frame, add_notes_button, 8, notes_to_display)

    update_task_button = customtkinter.CTkButton(master=edit_task_frame, width=300, height=60, fg_color="#2dbbd0",
                                                 text_color="white", font=app_font, text="Update Task",
                                                 command=lambda: submit_task(task_name, task_category, time_picker,
                                                                             task_priority_box, notes_frame,
                                                                             edit_window, "Update", task["id"]))
    update_task_button.grid(row=10, column=0, columnspan=2, pady=20)


def destroy_window(window):
    children = window.grid_slaves()
    for child in children:
        child.destroy()

    window.destroy()


def destroy_add_task(window):
    children = window.grid_slaves()
    for child in children:
        child.destroy()

    window.destroy()
    root.geometry("1300x750")


def reconfigure_task_note(task_note):
    new_note = ""
    counter = 0
    for i in range(len(task_note)):
        new_note += task_note[i]
        if counter > 35:
            if task_note[i] == " ":
                new_note += "\n"
                counter = 0

        counter += 1

    return new_note


def draw_tasks():
    row_counter = 1
    task_notes.clear()
    for i in range(len(task_list)):

        notes = []
        task_time = ""

        due_font_colour = "black"
        if task_list[i]["date_due"] <= date.today():
            due_font_colour = "red"

        if task_list[i]["task_finished"]:
            due_font_colour = "green"
            task_time += "Completed"
        else:
            task_time += str(task_list[i]["date_due"])
            if task_list[i]["time_due"] is not None:
                task_time += "\n"
                task_time += task_list[i]["time_due"].strftime("%I:%M %p")

        if task_list[i]["task_notes"] is not None:
            tasks_notes_frame = customtkinter.CTkScrollableFrame(master=right_frame, width=340, label_fg_color="black")
            tasks_notes_frame.grid(row=row_counter, column=1, sticky="ew", pady=2)

            note_counter = 0
            for task_note in task_list[i]["task_notes"]:
                if len(task_note) > 35:
                    new_task_note = reconfigure_task_note(task_note)
                    task_note = new_task_note

                task_note_checkbox = customtkinter.CTkCheckBox(master=tasks_notes_frame, font=app_font, text=task_note,
                                                               width=340)
                task_note_checkbox.grid(row=note_counter, column=0, pady=10, padx=10)
                notes.append(task_note_checkbox)
                note_counter += 1

            task_str = str(task_list[i]["task_name"])

            task_label_frame = customtkinter.CTkFrame(master=right_frame, width=400,
                                                      height=tasks_notes_frame.cget("height") + 14,
                                                      fg_color="#dbdbdb", )
            task_label_frame.grid(row=row_counter, column=0, padx=2, pady=2, sticky="nsew")

            task_label = customtkinter.CTkLabel(master=task_label_frame, width=400, height=30, font=task_font,
                                                text_color="black", text=task_str, corner_radius=5, fg_color="#dbdbdb")
            task_label.grid(row=0, column=0, padx=5, pady=(60, 0))

            task_options_frame = customtkinter.CTkFrame(master=task_label_frame, width=150, height=50,
                                                        fg_color="#dbdbdb")
            task_options_frame.grid(row=1, column=0)

            task_edit_button = customtkinter.CTkButton(master=task_options_frame, font=task_font, fg_color="#dbdbdb",
                                                       image=edit_image, text_color="black", text="", width=40,
                                                       height=40,
                                                       command=lambda i=i: create_edit_window(task_list[i],))
            task_edit_button.grid(row=0, column=0)

            task_complete_button = customtkinter.CTkButton(master=task_options_frame, font=task_font,
                                                           fg_color="#dbdbdb", image=checked_image, text_color="black",
                                                           text="", width=40, height=40,
                                                           command=lambda i=i, notes=notes: complete_task(task_list[i],
                                                                                                          notes))
            task_complete_button.grid(row=0, column=1, padx=(5, 0))

            task_delete_button = customtkinter.CTkButton(master=task_options_frame, font=task_font, fg_color="#dbdbdb",
                                                         image=delete_image, text="", width=40, height=40,
                                                         command=lambda i=i, notes=notes: delete_task(task_list[i],
                                                                                                      notes))
            task_delete_button.grid(row=0, column=2)

            task_due = customtkinter.CTkLabel(master=right_frame, width=240,
                                              height=tasks_notes_frame.cget("height") + 14, fg_color="#dbdbdb",
                                              corner_radius=5, text=task_time, font=app_font,
                                              text_color=due_font_colour)
            task_due.grid(row=row_counter, column=2, pady=2, padx=2)

        else:
            tasks_notes_checkbox = customtkinter.CTkLabel(master=right_frame, width=360, fg_color="#dbdbdb", height=100,
                                                          corner_radius=5, text="")
            tasks_notes_checkbox.grid(row=row_counter, column=1, pady=2)
            task_str = str(task_list[i]["task_name"])
            task_label_frame = customtkinter.CTkFrame(master=right_frame, width=400, fg_color="#dbdbdb")
            task_label_frame.grid(row=row_counter, column=0, padx=2, pady=2, sticky="nsew")

            task_label = customtkinter.CTkLabel(master=task_label_frame, width=400, height=30, font=task_font,
                                                text_color="black", text=task_str, corner_radius=5, fg_color="#dbdbdb")
            task_label.grid(row=0, column=0, padx=5, pady=(12, 0))

            task_options_frame = customtkinter.CTkFrame(master=task_label_frame, width=150, height=50,
                                                        fg_color="#dbdbdb")
            task_options_frame.grid(row=1, column=0)

            task_edit_button = customtkinter.CTkButton(master=task_options_frame, font=task_font, fg_color="#dbdbdb",
                                                       image=edit_image, text_color="black", text="", width=40,
                                                       height=40, command=lambda i=i: create_edit_window(task_list[i]))
            task_edit_button.grid(row=0, column=0)

            task_complete_button = customtkinter.CTkButton(master=task_options_frame, font=task_font,
                                                           fg_color="#dbdbdb",
                                                           image=checked_image, text_color="black", text="", width=40,
                                                           height=40, command=lambda i=i: complete_task(task_list[i]))
            task_complete_button.grid(row=0, column=1, padx=(5, 0))

            task_delete_button = customtkinter.CTkButton(master=task_options_frame, font=task_font, fg_color="#dbdbdb",
                                                         image=delete_image, text="", width=40, height=40,
                                                         command=lambda i=i: delete_task(task_list[i]))
            task_delete_button.grid(row=0, column=2)

            task_due = customtkinter.CTkLabel(master=right_frame, width=240, height=102,
                                              fg_color="#dbdbdb", corner_radius=5, text=task_time, font=app_font,
                                              text_color=due_font_colour)
            task_due.grid(row=row_counter, column=2, pady=2, padx=1)

        task_notes.append(notes)
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


def draw_titles():
    to_do_title_label = customtkinter.CTkLabel(master=right_frame, justify="center", font=app_font, fg_color="#232323",
                                               width=400, height=62, pady=20, padx=1, text_color="white",
                                               text="To-Do List")
    to_do_title_label.grid(row=0, column=0, rowspan=1)

    notes_title_label = customtkinter.CTkLabel(master=right_frame, justify="center", font=app_font, fg_color="#232323",
                                               corner_radius=4, width=340, pady=20, text_color="white", text="Notes")
    notes_title_label.grid(row=0, column=1)

    add_task_button = customtkinter.CTkButton(master=right_frame, width=200, height=50, fg_color="#2dbbd0",
                                              text_color="white", text="Add Task", command=create_add_task)
    add_task_button.grid(row=0, column=2)


def redraw_tasks():
    for widget in right_frame.winfo_children():
        widget.destroy()

    get_tasks()
    draw_titles()
    draw_tasks()
    root.update()


def redraw_categories():
    for widget in left_frame.winfo_children():
        widget.destroy()

    left_title_label = customtkinter.CTkLabel(master=left_frame, justify="center", font=app_font, fg_color="#232323",
                                              width=248, height=62, pady=20, padx=1, text_color="white",
                                              text="Categories")
    left_title_label.grid(row=0, column=0)
    draw_categories()
    button_row = len(category_buttons) + 2
    filter_button = customtkinter.CTkButton(master=left_frame, width=200, height=50, fg_color="#232323",
                                            text_color="white", text="Apply filters", command=redraw_tasks)
    filter_button.grid(row=button_row, column=0)
    root.update()


def open_calendar(due_date_frame, task_date_due):
    window = customtkinter.CTkToplevel(fg_color="#232323")
    window.geometry("280x250")
    window.transient(master=due_date_frame)

    year = datetime.today().year
    month = datetime.today().month
    day = datetime.today().day

    cal = Calendar(master=window, selectmode='day', year=year, month=month, day=day, font=app_font,
                   date_pattern="y-mm-dd")
    cal.grid(row=0, column=0, pady=5)

    cal_button = customtkinter.CTkButton(master=window, width=100, fg_color="#dbdbdb", text_color="black",
                                         text="Select Due Date",
                                         command=lambda: select_date(task_date_due, window, cal))

    cal_button.grid(row=1, column=0)


def select_date(task_date_due, window, cal):
    global due_date
    selected_date = cal.get_date()
    due_date = selected_date
    task_date_due.configure(text=selected_date)
    window.destroy()


def add_time_picker(time_picker_frame, time_picker, time_picker_row, time_picker_button):
    time_picker_button.grid_remove()

    global time_selected
    time_selected = True

    time_picker_frame.grid(row=time_picker_row, column=0, columnspan=2)

    time_picker_label = customtkinter.CTkLabel(master=time_picker_frame, width=80, font=app_font, fg_color="#232323",
                                               text_color="white", text="Optional Time Deadline: ")
    time_picker_label.grid(row=0, column=0, padx=10)

    time_picker.grid(row=0, column=1, padx=20)

    time_picker_exit = customtkinter.CTkButton(master=time_picker_frame, width=25, fg_color="#f3050a", font=exit_font,
                                               text_color="white", text="X",
                                               command=lambda: destroy_time_picker(time_picker, time_picker_frame,
                                                                                   time_picker_row, time_picker_button))
    time_picker_exit.grid(row=0, column=2)


def destroy_time_picker(time_picker, time_picker_frame, time_picker_row, time_picker_button):
    global time_selected
    time_selected = False
    time_picker.grid_remove()
    time_picker_frame.grid_remove()

    time_picker_button.grid(row=time_picker_row, column=0, columnspan=2, pady=5)


def add_note_section(add_task_frame, notes_frame, add_notes_button, notes_row, notes_to_display):
    add_notes_button.grid_remove()
    notes_frame.grid(row=notes_row, column=0, columnspan=2, pady=10)

    notes_title = customtkinter.CTkLabel(master=notes_frame, width=80, font=app_font, fg_color="#232323",
                                         text_color="white", text="Notes: ")
    notes_title.grid(row=0, column=0, columnspan=2)

    add_note_entry = customtkinter.CTkButton(master=add_task_frame, width=350, height=40, font=app_font,
                                             text_color="white", fg_color="#232323", text="+ Add Note",
                                             command=lambda: create_note_entry(notes_frame, add_notes_button,
                                                                               add_note_entry, notes_row))
    add_note_entry.grid(row=notes_row + 1, column=0, columnspan=2)

    if len(notes_to_display) == 0:
        create_note_entry(notes_frame, add_notes_button, add_note_entry, notes_row)
    else:
        for note in notes_to_display:
            create_note_entry(notes_frame, add_notes_button, add_note_entry, notes_row, note)


def create_note_entry(notes_frame, add_notes_button, add_note_entry, notes_row, note_text=None):
    global new_note_counter
    if note_text is None:
        note_entry = customtkinter.CTkEntry(master=notes_frame, width=250, font=app_font, text_color="black",
                                            placeholder_text="New Note")
    else:
        note_stringvar = customtkinter.StringVar(value=note_text)
        note_entry = customtkinter.CTkEntry(master=notes_frame, width=250, font=app_font, text_color="black",
                                            textvariable=note_stringvar)
    note_entry.grid(row=new_note_counter, column=0, pady=5)

    note_delete = customtkinter.CTkButton(master=notes_frame, width=25, fg_color="#f3050a", font=exit_font,
                                          text_color="white", text="X",
                                          command=lambda: delete_note(note_delete, add_notes_button, add_note_entry,
                                                                      note_entry, notes_row))
    note_delete.grid(row=new_note_counter, column=1, padx=5)

    new_note_counter += 1
    new_note_list.append(note_entry)


def delete_note(note_delete, add_notes_button, add_note_entry, note_entry, notes_row):
    global new_note_counter
    note_entry.destroy()
    note_delete.destroy()
    new_note_counter -= 1
    new_note_list.remove(note_entry)
    if new_note_counter == 1:
        add_note_entry.destroy()
        add_notes_button.grid(row=notes_row + 1, column=0, columnspan=2, pady=10)


# noinspection DuplicatedCode
def create_add_task():
    root.geometry("1680x750")

    global due_date
    global time_selected
    notes_to_display = []

    add_task_frame = customtkinter.CTkScrollableFrame(master=root, width=400, height=750, fg_color="#232323")
    add_task_frame.place(x=1280, y=0)

    add_task_title = customtkinter.CTkLabel(master=add_task_frame, width=330, height=62, font=task_font,
                                            text="Add task", text_color="white")
    add_task_title.grid(row=0, column=0)

    close_button = customtkinter.CTkButton(master=add_task_frame, width=40, fg_color="#232323", font=exit_font,
                                           text_color="white", text="X",
                                           command=lambda: destroy_add_task(add_task_frame))
    close_button.grid(row=0, column=1)

    task_name = customtkinter.CTkEntry(master=add_task_frame, width=350, height=30, font=app_font,
                                       placeholder_text="Task Name")
    task_name.grid(row=1, column=0, pady=5)

    task_category = customtkinter.CTkEntry(master=add_task_frame, width=350, height=30, font=app_font,
                                           placeholder_text="Default: Other")
    task_category.grid(row=2, column=0, pady=5)

    due_date_frame = customtkinter.CTkFrame(master=add_task_frame, width=400, height=40, fg_color="#232323",
                                            corner_radius=5)
    due_date_frame.grid(row=3, column=0, pady=5)

    due_label = customtkinter.CTkLabel(master=due_date_frame, text="Due: ", font=app_font, text_color="white", width=50,
                                       height=40, fg_color="#232323")
    due_label.grid(row=0, column=0, pady=5)

    task_date_due = customtkinter.CTkButton(master=due_date_frame, text=due_date, text_color="white",
                                            fg_color="#1f1e1c", width=300, height=40, font=app_font,
                                            command=lambda: open_calendar(due_date_frame, task_date_due))
    task_date_due.grid(row=0, column=1, pady=5)

    # create time picker without displaying
    time_picker_frame = customtkinter.CTkFrame(master=add_task_frame, width=350, height=40, fg_color="#232323")

    time_picker = SpinTimePickerModern(time_picker_frame)
    time_picker.addAll(constants.HOURS12)
    time_picker.configureAll(bg="#404040", height=1, fg="#dbdbdb", font=app_font, hoverbg="#dbdbdb",
                             hovercolor="#2dbbd0", clickedbg="#dbdbdb", clickedcolor="#2dbbd0")
    time_picker.configure_separator(bg="#404040", fg="#ffffff")
    # -------------------------------------

    time_picker_button = customtkinter.CTkButton(master=add_task_frame, width=300, height=30, fg_color="#dbdbdb",
                                                 text_color="black", font=app_font, text="Set Optional Time Deadline",
                                                 command=lambda:
                                                 add_time_picker(time_picker_frame, time_picker, 4, time_picker_button))
    time_picker_button.grid(row=4, column=0, pady=5)

    task_priority_frame = customtkinter.CTkFrame(master=add_task_frame, width=400, height=30, fg_color="#232323")
    task_priority_frame.grid(row=5, column=0, pady=10)

    task_priority_label = customtkinter.CTkLabel(master=task_priority_frame, width=30, font=app_font,
                                                 text_color="white", text="Task Priority: ")
    task_priority_label.grid(row=0, column=0, padx=10)

    task_priority_box = customtkinter.CTkComboBox(master=task_priority_frame, fg_color="#1f1e1c",
                                                  values=["1", "2", "3", "4", "5"], font=app_font, text_color="white")
    task_priority_box.set("1")
    task_priority_box.grid(row=0, column=1)

    notes_frame = customtkinter.CTkFrame(master=add_task_frame, width=350, fg_color="#232323")

    add_notes_button = customtkinter.CTkButton(master=add_task_frame, width=300, height=30, fg_color="#dbdbdb",
                                               text_color="black", font=app_font, text="Add Notes",
                                               command=lambda: add_note_section(add_task_frame, notes_frame,
                                                                                add_notes_button, 6, notes_to_display))
    add_notes_button.grid(row=6, column=0, pady=10)

    add_new_task = customtkinter.CTkButton(master=add_task_frame, width=300, height=60, fg_color="#2dbbd0",
                                           text_color="white", font=app_font, text="Submit New Task",
                                           command=lambda: submit_task(task_name, task_category, time_picker,
                                                                       task_priority_box, notes_frame, add_task_frame,
                                                                       "Add"))
    add_new_task.grid(row=8, column=0, pady=20)


create_table()

left_frame = customtkinter.CTkFrame(master=root, width=250, height=750, fg_color="#1f1e1c")
left_frame.place(x=0, y=0)

right_frame = customtkinter.CTkScrollableFrame(master=root, width=1000, height=750, fg_color="#232323",
                                               scrollbar_button_color="white")
right_frame.place(x=250, y=0)

left_title_label = customtkinter.CTkLabel(master=left_frame, justify="center", font=app_font, fg_color="#232323",
                                          width=248, height=62, pady=20, padx=1, text_color="white", text="Categories")
left_title_label.grid(row=0, column=0)

draw_categories()
get_tasks()

button_row = len(category_buttons) + 2
filter_button = customtkinter.CTkButton(master=left_frame, width=200, height=50, fg_color="#232323", text_color="white",
                                        text="Apply filters", command=redraw_tasks)
filter_button.grid(row=button_row, column=0)

draw_titles()

draw_tasks()

root.mainloop()
