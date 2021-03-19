from flask import Flask, render_template
import sqlite3
from flask import Flask, render_template
import os
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename
from flask import send_from_directory
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/')
def vertical():
    return render_template('vertical.html')

@app.route('/generate-adhesion/')
def generate_adhesion():
  print ('I got clicked!')
  return 'Click.'


UPLOAD_FOLDER = '/gcode'
ALLOWED_EXTENSIONS = {'gcode'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/uploader', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        f.save(secure_filename(f.filename))
        return


if __name__ == '__main__':
  app.run(debug=True)