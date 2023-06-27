from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
import os

app = Flask(__name__)
key = os.urandom(20)
app.secret_key = key

@app.route("/")
def homepage():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)