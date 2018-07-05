#!/home/ider/anaconda3/bin/python

import os, time, zipfile, tempfile, uuid, shutil, subprocess
from flask import Flask, request, send_from_directory, send_file
from werkzeug.utils import secure_filename
app = Flask(__name__)


UPLOAD_FOLDER = '/tmp'
bin = "/usr/local/bin/pdf2htmlEX"
ALLOWED_EXTENSIONS = set(['pdf',])


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['COUNT'] = 0
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = os.urandom(24)
app.config['COUNT'] = 0

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/pdf2htmlEX', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files or 'command' not in request.form:
            return "no file", 404
        file = request.files['file']
        command = request.form['command']
        if file.filename == '':
            return "no filename", 404

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            try:
                fp = pdf2htmlEX(file_path, command)
            except Exception as e:
                return str(e),500
            app.config['COUNT'] += 1
            return send_file(fp,as_attachment=True,attachment_filename='%s.zip'%filename.split('.')[0])
            # return "ok" + command, 200
    elif request.method == 'GET':
        return 'Completing %s document conversions'%app.config['COUNT']
    return "unknow error", 500

def pdf2htmlEX(pdf_path,command):
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], str(uuid.uuid4()))
    os.mkdir(folder_path)
    cmd = [bin,]
    cmd.extend(command.split(' '))

    cmd.extend(['--dest-dir',folder_path,pdf_path])

    subprocess.check_output(cmd)

    # shutil.copy(pdf_path,os.path.join(pdf_path,folder_path))

    fp = tempfile.TemporaryFile()
    with zipfile.ZipFile(fp, 'w') as myzip:
        for obj in os.walk(folder_path):
            for file in obj[2]:
                file_path = obj[0] + os.sep + file
                myzip.write(file_path,arcname=file_path.replace(folder_path,'').lstrip('/'))
    shutil.rmtree(folder_path)
    os.remove(pdf_path)
    fp.seek(0)
    return fp


if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5000)
