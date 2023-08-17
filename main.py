import random
import pymysql
from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory, Response, jsonify, session
from wtforms import StringField, SubmitField, validators, IntegerField, FloatField, TextAreaField
from wtforms.fields import EmailField
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from flask_ckeditor import CKEditor, CKEditorField
from wtforms.validators import DataRequired
import os
from dotenv import load_dotenv
from smtplib import SMTP, SMTPResponseException, SMTPAuthenticationError, SMTPSenderRefused
import database_connection as db
import lxml.html
import lxml.html.clean
from base64 import b64encode
from flask_socketio import join_room, leave_room, send, SocketIO, emit

app = Flask(__name__)
key = os.urandom(20)
app.secret_key = key
Bootstrap(app)
ckeditor = CKEditor(app)
socketio = SocketIO(app)

load_dotenv()
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
CHATBOX_EMAIL = os.getenv('CHATBOX_EMAIL')

UPLOAD_FOLDER = 'images'
ALLOWED_EXTENSTION = {"png", "jpg", "jpeg", "gif"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# List of rooms created
rooms = {}
rooms_code = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O',
              'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']


# --------- FLASK FORM
class SendMessage(FlaskForm):
    company_name = StringField(
        label="Company/Personal Name",
        validators=[validators.DataRequired()]
    )
    company_email = EmailField(
        label="Email",
        validators=[validators.DataRequired()])
    message = TextAreaField(
        label="Message",
        validators=[DataRequired()]
    )
    submit = SubmitField(
        label="Send Message"
    )


class AddProject(FlaskForm):
    project_name = StringField(label="Project Name", validators=[DataRequired()])
    project_detail = CKEditorField(label="Project Detail", validators=[DataRequired()])
    project_code_overview = CKEditorField(label="Code Overview", validators=[DataRequired()])
    project_image = FileField(label="Project Image")
    submit = SubmitField(label="Add Projects")


def send_email(name, email, message):
    error_message = {
        "message": "Upss... Your email has not been sent, please send again\n\n:(",
        "category": "error"}
    success_message = {
        "message": "Your message has been sent to contact@rickykristianbutarbutar.com.\nI will reply shortly.",
        "category": "success"
    }
    with SMTP(host="smtp.gmail.com", port=587) as connection:
        connection.starttls()
        try:
            connection.login(user=SENDER_EMAIL, password=EMAIL_PASSWORD)
            connection.sendmail(
                from_addr=SENDER_EMAIL,
                to_addrs=RECIPIENT_EMAIL,
                msg=f"Subject:Mail From Portofolio Website\n\n"
                    f"FROM: {name}\nEMAIL: {email}\nMESSAGE: \n\n{message}"
            )
        except SMTPSenderRefused:
            flash(error_message["message"], error_message["category"])
            response = error_message
        except SMTPAuthenticationError:
            flash(error_message["message"], error_message["category"])
            response = error_message
        except SMTPResponseException:
            flash(error_message["message"], error_message["category"])
            response = error_message
        else:
            flash(success_message["message"], success_message["category"])
            response = success_message
    return response


def clean_projects(direct_to=None):
    """To remove all html tag from all project"""
    if direct_to == "homepage":
        all_projects = db.project_list(direct_to=direct_to)
    else:
        all_projects = db.project_list()
    for project in all_projects:
        for key, value in project.items():
            if isinstance(value, str):
                text = lxml.html.fromstring(value)
                cleaner = lxml.html.clean.Cleaner(style=True)
                text = cleaner.clean_html(text)
                project[key] = text.text_content()
            if key == "project_img":
                project[key] = b64encode(value).decode("utf-8")  ## encode image binary
    return all_projects


def clean_one_project(id):
    """To remove all html tag from 1 project"""
    project = db.retrieve_project(id)
    for key, value in project.items():
        if isinstance(value, str):
            text = lxml.html.fromstring(value)
            cleaner = lxml.html.clean.Cleaner(style=True)
            text = cleaner.clean_html(text)
            project[key] = text.text_content()
        if key == "project_img":
            project[key] = b64encode(value).decode("utf-8")  ## encode image binary
    return project


# TODO: make this send email method to send email and clear form without refresh the page (ASYNC)
@app.route("/", methods=['GET', 'POST'])
def homepage():
    """Homepage to show profile. Include pagination for project list"""
    session.clear()  # clear session everytime enter homepage
    all_projects = clean_projects(direct_to="homepage")
    message_form = SendMessage()
    form_for = "homepage"  # to tell the message form at the footer is accessed from homepage
    if request.method == "POST":
        # send email
        message = request.form.get("message")
        email = request.form.get("company_email")
        name = request.form.get("company_name")

        send_email_response = send_email(name=name, email=email, message=message)

        return jsonify(send_email_response)
    return render_template("index.html", form=message_form, form_for=form_for, projects=all_projects[:8])


def generate_room(length: int):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(rooms_code)

        if code not in rooms:
            break

    return code


@app.route("/api/chat-box", methods=["GET", "POST"])
def chatbox():
    data = request.get_json()
    name = data.get("name")

    if not name:
        print("Ga ada nama")
        response_data = {
            "message": "Please Enter Your Name",
            'category': 'error'
        }
        return jsonify(response_data)
    # Generate rooms code
    room_code = generate_room(5)

    rooms[room_code] = {
        "members_name": [],
        "members": 0,
        "messages": [],
        "counter": 0
    }

    session["room"] = room_code
    session["name"] = name
    session["usercode"] = 2  # To differentiate between Ricky and Other person. 2 for other person, 1 for Ricky

    # Returning a response back to the frontend
    messages = rooms[room_code]["messages"]
    return jsonify(messages)


@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    usercode = session.get("usercode")

    if not room and not name:
        return
    if room not in rooms:
        leave_room(room)
        return

    join_room(room)

    # Send email to Ricky which contains the link to the center chat box
    if usercode != 1:
        with SMTP(host="smtp.gmail.com", port=587) as connection:
            connection.starttls()
            try:
                connection.login(user=SENDER_EMAIL, password=EMAIL_PASSWORD)
                connection.sendmail(
                    from_addr=SENDER_EMAIL,
                    to_addrs=CHATBOX_EMAIL,
                    msg=f"Subject:NEW CHAT BOX\n\n"
                        f"FROM: {name}\nROOM CODE: {room}\nMESSAGE: \n\nrickykristianbutarbutar.com/center-chatbox/{room}"
                )
            except Exception as err:
                print(err)

    rooms[room]["members"] += 1
    rooms[room]["counter"] += 1
    rooms[room]["members_name"].append(name)
    send({'name': name, "message": "has entered the chat"}, to=room)

    if rooms[room]["counter"] == 1:
        send({'waiting_message': "Wait for Ricky to enter the chat ......"}, to=room)
    print(f"{name} has entered the chat: {room}")


@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 1:
            del rooms[room]

    send({"name": name, "message": "has left the chat. This chat is no longer exist"}, to=room)
    print(f"{name} has left the chat")


@socketio.on("message")
def message(data):
    room = session.get("room")
    name = session.get("name")
    if room and name:
        message = data.get("data")
        if message:
            message_data = {
                "name": name,
                "message": message,
            }
            rooms[room]["messages"].append(message_data)
            emit("message", message_data, room=room)


@app.route("/center-chatbox/<string:room>")
def center_chat(room):
    session["name"] = "Ricky"
    session["room"] = room
    session["usercode"] = 1

    return render_template("center-chatbox.html",
                           messages=rooms[room]["messages"],
                           client=rooms[room]["members_name"][0]
                           )


@app.route("/download-resume/<path:filename>")
def download_resume(filename):
    """To Download Resume"""
    return send_from_directory('static', filename)


def allowed_file(filename):
    """To restrict which file types can be accepted"""
    return "." in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSTION


@app.route("/add-projects", methods=["GET", "POST"])
def add_projects():
    """To add project to database"""
    add_projects_form = AddProject()
    if request.method == "POST":
        if "project_image" not in request.files:
            error_message = {
                "message": "No file chosen",
                "category": "error"
            }
            flash(error_message["message"], error_message["category"])
            response = error_message
            return response
        file = request.files["project_image"]
        if file.filename == "":
            error_message = {
                "message": "No selected File",
                "category": "error"
            }
            flash(error_message["message"], error_message["category"])
            response = error_message
            return response

        if file and allowed_file(file.filename):
            image_data = file.read()
            details = {
                "project_name": add_projects_form.project_name.data,
                "project_overview": add_projects_form.project_detail.data,
                "project_code_overview": add_projects_form.project_code_overview.data,
                "project_img": image_data
            }
            try:
                db.save_add_project_detail(details=details)
            except pymysql.Error as err:
                error_message = {
                    "message": f"Database Error: {str(err)}",
                    "category": "error"
                }
                flash(error_message["message"], error_message["category"])
                response = error_message
                return response
            else:
                success_message = {
                    "message": "Add project is success",
                    "category": "success"
                }
                flash(success_message["message"], success_message["category"])
                response = success_message
                return jsonify(response)
        else:
            error_message = {
                "message": "File type is not supported",
                "category": "error"
            }
            flash(error_message["message"], error_message["category"])
            response = error_message
            return jsonify(response)
    return render_template("add-projects.html", form=add_projects_form)


@app.route("/project-details/<int:id>", methods=["GET", "POST"])
def project_details(id):
    """Get the details of the projects"""
    try:
        project = clean_one_project(id)
    except pymysql.Error as err:
        flash(f"Database Error: {str(err)}", "error")
    except AttributeError:
        flash(f"There is no project yet in database. Add first!!", "error")
        return redirect(url_for("add_projects"))
    message_form = SendMessage()
    form_for = "project_details"  # To differentiate message from in project details page with other page
    if request.method == "POST":
        message = request.form.get("message")
        email = request.form.get("company_email")
        name = request.form.get("company_name")
        send_email_response = send_email(name=name, email=email, message=message)
        return jsonify(send_email_response)

    return render_template("project-details.html", form=message_form, form_for=form_for, project=project, id=id)


@app.route('/all_projects', methods=["GET"])
def projects_list():
    all_projects = clean_projects()
    return render_template('all_projects.html', projects=all_projects)


if __name__ == "__main__":
    app.run()
