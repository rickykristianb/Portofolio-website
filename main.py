from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory
from wtforms import StringField, SubmitField, validators, IntegerField, FloatField, TextAreaField
from wtforms.fields import EmailField
from flask_bootstrap import Bootstrap
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_wtf import FlaskForm
from flask_ckeditor import CKEditor, CKEditorField
from wtforms.validators import DataRequired, URL, Length
import os
from dotenv import load_dotenv
from smtplib import SMTP, SMTPResponseException, SMTPAuthenticationError, SMTPSenderRefused
import base64
import mysql.connector as mc


app = Flask(__name__)
key = os.urandom(20)
app.secret_key = key
Bootstrap(app)
ckeditor = CKEditor(app)

load_dotenv()
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')


class SendMessage(FlaskForm):
    company_name = StringField(label="Company/Personal Name",
        validators=[validators.DataRequired()]
    )
    company_email = EmailField(label="Email", validators=[validators.DataRequired()])
    message = TextAreaField(label="Message",
        validators=[DataRequired()]
    )
    submit = SubmitField(label="Send Message")


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


@app.route("/", methods=['GET', 'POST'])
def homepage():
    message_form = SendMessage()
    if request.method == "POST" and message_form.validate_on_submit():
        message = message_form.message.data
        email = message_form.company_email.data
        name = message_form.company_name.data
        send_email(name=name, email=email, message=message)
        return redirect(url_for("homepage"))

    return render_template("index.html", form=message_form)


@app.route("/download-resume/<path:filename>")
def download_resume(filename):
    return send_from_directory('static', filename)


@app.route("/add-projects")
@login_required
def add_projects():
    return render_template("add-projects.html")


if __name__ == "__main__":
    app.run(debug=True)