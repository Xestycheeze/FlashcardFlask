from flask import Flask, render_template, url_for, redirect, request
from pathlib import Path
app = Flask(__name__)

@app.route('/home')
@app.route('/')
def home():
    return render_template("home.html")

# Make the following routes: /sets (to display all sets, method=GET), /sets/create_sets (to create sets, method=POST), /sets/set/<int:set_id> (to display all cards in a specific set, method=GET)
# Please make the database, so that Kate can start creating routes thx

if __name__ == '__main__':
    app.run(debug=True, port=8000)
