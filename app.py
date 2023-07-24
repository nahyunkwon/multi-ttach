from flask import Flask, render_template
import sqlite3
from flask import Flask, render_template
import os
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename
from flask import send_from_directory
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import time
from flask import Flask, render_template
from vertical_adhesion import *
from horizontal_adhesion import *

app = Flask(__name__, static_url_path='')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/js/Worker.js')
#def send_js():
#    return render_template('Worker.js')

#@app.route('/about/')
def about():
    return render_template('about.html')

UPLOAD_FOLDER = "user_files"
ALLOWED_EXTENSIONS = {'.gcode'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/uploader_1', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        f.save("./user_files/" + secure_filename(f.filename))

        layers = request.form['layers']
        temps = request.form['temperatures']
        type = request.form['options']

        if type == 'bead':
            type = 'blob'
        elif type == 'lattice':
            type = 'grid'

        layers_list = layers.split(",")
        
        layers_input = []
        for i in range(len(layers_list)):
            layers_input.append(int(layers_list[i].strip()))

        temps_input = [x.strip() for x in temps.split(",")]

        file_name = "./user_files/" + f.filename
        adhesion_type = type
        target_layers = layers_input
        temps = temps_input
        adhesion_structure_vertical(file_name, adhesion_type, target_layers, temps)
        #adhesion_structure_vertical("./user_files/" + f.filename, layers_input, type, temps_input)

        output_file = f.filename.split(".gcode")[0]+"_"+type+".gcode"
        time.sleep(5)
        return send_from_directory(directory=UPLOAD_FOLDER, filename=output_file, as_attachment=True)


@app.route('/uploader_2', methods=['GET', 'POST'])
def upload_file_2():
    if request.method == 'POST':
        f = request.files['file']
        f.save("./user_files/" + secure_filename(f.filename))

        type = request.form['options']

        if type == 'bead':
            type = 'blob'
        elif type == 'lattice':
            type = 'grid'

        adhesion_structure_vertical_for_dual_extruder("./user_files/" + f.filename, type)

        output_file = f.filename.split(".gcode")[0] + "_" + type + ".gcode"
        time.sleep(5)
        return send_from_directory(directory="user_files", filename=output_file, as_attachment=True)


@app.route('/uploader_3', methods=['GET', 'POST'])
def upload_file_3():
    if request.method == 'POST':
        f = request.files['file']
        f.save("./user_files/" + secure_filename(f.filename))

        adhesion_structure_horizontal("./user_files/" + f.filename)

        output_file = f.filename.split(".gcode")[0] + "_stitched" + ".gcode"
        time.sleep(5)
        return send_from_directory(directory="user_files", filename=output_file, as_attachment=True)


if __name__ == '__main__':
    if 'liveconsole' not in gethostname():
        app.run(debug=True)