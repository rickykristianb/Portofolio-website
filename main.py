import pymysql
from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory, Response
from wtforms import StringField, SubmitField, validators, IntegerField, FloatField, TextAreaField
from wtforms.fields import EmailField
from flask_bootstrap import Bootstrap
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from flask_ckeditor import CKEditor, CKEditorField
from wtforms.validators import DataRequired, URL, Length
import os
from dotenv import load_dotenv
from smtplib import SMTP, SMTPResponseException, SMTPAuthenticationError, SMTPSenderRefused
import database_connection as db
import lxml.html
import lxml.html.clean
from base64 import b64encode
from flask import Blueprint
from flask_paginate import Pagination, get_page_parameter


app = Flask(__name__)
key = os.urandom(20)
app.secret_key = key
Bootstrap(app)
ckeditor = CKEditor(app)

load_dotenv()
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

UPLOAD_FOLDER = 'images'
ALLOWED_EXTENSTION = {"png", "jpg", "jpeg", "gif"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


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
    project_name = StringField(validators=[DataRequired()])
    project_detail = CKEditorField(validators=[DataRequired()])
    project_code_overview = CKEditorField(label="Code Overview", validators=[DataRequired()])
    project_image = FileField(label="Project Image")
    submit = SubmitField(label="Add Projects")


def send_email(name, email, message):
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
            flash("Upss... Your email has not been sent, please send again\n\n:(", "error")
        except SMTPAuthenticationError:
            flash("Upss... Your email has not been sent, please send again\n\n:(", "error")
        except SMTPResponseException:
            flash("Upss... Your email has not been sent, please send again\n\n:(", "error")
        else:
            flash("Your message has been sent to ricky.kristianb@gmail.com.\nI will reply shortly", "success")


def clean_projects():
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


def pagination():
    search = False
    all_projects = clean_projects()
    if all_projects:
        search = True
    total_projects = db.count_projects()
    page = request.args.get(get_page_parameter(), type=int, default=1)
    pagination = Pagination(page=page, total=total_projects, search=search, record_name="projects")
    return pagination


# TODO: make this send email method to send email and clear form without refresh the page (ASYNC)
@app.route("/", methods=['GET', 'POST'])
def homepage():
    pagination()
    all_projects = clean_projects()
    message_form = SendMessage()
    form_for = "homepage"
    if request.method == "POST" and message_form.validate_on_submit():
        message = message_form.message.data
        email = message_form.company_email.data
        name = message_form.company_name.data
        send_email(name=name, email=email, message=message)
        # return redirect(url_for("homepage"))
        return redirect("/#contact-page")
    return render_template("index.html", form=message_form, form_for=form_for, projects=all_projects, pagination=pagination)


@app.route("/download-resume/<path:filename>")
def download_resume(filename):
    return send_from_directory('static', filename)


def allowed_file(filename):
    return "." in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSTION


@app.route("/add-projects", methods=["GET", "POST"])
def add_projects():
    add_projects_form = AddProject()
    if request.method == "POST":
        if "project_image" not in request.files:
            flash("No file part", "error")
            return redirect(request.url)
        file = request.files["project_image"]
        if file.filename == "":
            flash("No selected File", "error")
            return redirect(request.url)
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
                flash(f"Database Error: {str(err)}", "error")
            else:
                flash("Add project is success", "success")
            return redirect(url_for("add_projects"))
        else:
            flash("File type is not supported", "error")
    return render_template("add-projects.html", form=add_projects_form)


@app.route("/project-details/<int:id>", methods=["GET", "POST"])
def project_details(id):
    try:
        project = clean_one_project(id)
    except pymysql.Error as err:
        flash(f"Database Error: {str(err)}", "error")
    except AttributeError:
        flash(f"There is no project yet in database. Add first!!", "error")
        return redirect(url_for("add_projects"))
    message_form = SendMessage()
    form_for = "project_details"
    if request.method == "POST" and message_form.validate_on_submit():
        message = message_form.message.data
        email = message_form.company_email.data
        name = message_form.company_name.data
        send_email(message=message, email=email, name=name)
        return redirect(url_for("project_details") + "#contact-page")
    return render_template("project-details.html", form=message_form, form_for=form_for, project=project, id=id)


if __name__ == "__main__":
    app.run(debug=True)