import os
import json
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from flask_moment import Moment
import google.generativeai as genai # 1. Import the library
from PIL import Image # For handling image uploads

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

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-3.1-flash-lite')


@app.route('/', methods=["GET", "POST"])
def main_page():
    if request.method == "GET":
        return render_template("index.html")
    else:
        instructions = request.form.get("instructions")
        deadline = request.form.get("date")
        num_people = request.form.get("number")

        if int(num_people) < 1:
            return render_template("index.html", error="You need at least one person!")

        uploaded_files = request.files.getlist("images")
        file_paths = []
        gemini_images = []  # Images formatted for the API

        for file in uploaded_files:
            if file and file.filename:
                path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(path)
                file_paths.append(path)
                # Load image for Gemini
                img = Image.open(path)
                gemini_images.append(img)

        # 3. Create the Prompt
        prompt = f"""
        Analyze this assignment and split it into a fair workload for {num_people} people.
        The final deadline is {deadline}.

        Instructions: {instructions}

        Return the response as a JSON object with this structure:
        {{
          "plan": [
            {{ "student": 1, "task": "description", "difficulty": "1-10", "deadline": "YYYY-MM-DD" }}
          ]
        }}
        """

        # 4. Call the API
        try:
            # Send prompt + any images found
            content_to_send = [prompt] + gemini_images
            response = model.generate_content(content_to_send)

            # Clean the response (sometimes AI adds markdown code blocks)
            raw_text = response.text.replace('```json', '').replace('```', '').strip()
            project_plan = json.loads(raw_text)

            return render_template("index.html",
                                   success=True,
                                   file_paths=file_paths,
                                   plan=project_plan['plan'])
        except Exception as e:
            print(f"Error: {e}")
            return render_template("index.html", error="Failed to process project.")
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
    app.run(port=2423)
