import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from flask_moment import Moment

app_path = os.path.join(os.path.dirname(__file__), '.')
dotenv_path = os.path.join(app_path, '.env')
load_dotenv(dotenv_path)

connection_string = os.environ.get("MONGO_STRING")
cluster = MongoClient(connection_string)
database = cluster["GroupProjectSplitter"]
collection = database["login"]
app = Flask(__name__)
moment = Moment(app)
app.secret_key = os.environ.get("SECRET_KEY")

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=["GET", "POST"])
def main_page():
    if request.method == "GET":
        return render_template("index.html")
    else:
        instructions = request.form.get("instructions")
        deadline = request.form.get("date")
        num_people = request.form.get("number")
        
        uploaded_files = request.files.getlist("images")
        file_paths = []
        for file in uploaded_files:
            if file and file.filename:
                filename = file.filename
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(path)
                file_paths.append(path)
        
        return render_template("index.html", success=True, file_paths=file_paths)

@app.route('/delete_image', methods=['POST'])
def delete_image():
    data = request.json
    file_path = data.get('path')
    if file_path and os.path.exists(file_path):
        try:
            # Basic security check to ensure we only delete from uploads folder
            if 'static/uploads' in file_path:
                os.remove(file_path)
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Unauthorized path'}), 403
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    return jsonify({'success': False, 'error': 'File not found'}), 404

if __name__ == '__main__':
    app.run(port=2423, debug=True)
