from flask import Flask, render_template, url_for, redirect, request
from pathlib import Path
app = Flask(__name__)


@app.route('/')
def hello_world():  # put application's code here
    return render_template("home.html")


if __name__ == '__main__':
    app.run(debug=True, port=8000)
