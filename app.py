from flask import Flask, request, render_template_string
import os
import zipfile
import hashlib
from datetime import datetime

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Digital Declutter Assistant</title>
    <style>
        body {
            font-family: Arial;
            text-align: center;
            background-color: #f4f6f8;
            padding-top: 50px;
        }
        .card {
            background: white;
            padding: 25px;
            margin: auto;
            width: 450px;
            border-radius: 12px;
            box-shadow: 0px 5px 15px rgba(0,0,0,0.1);
        }
        button {
            padding: 8px 15px;
            border: none;
            background: #4CAF50;
            color: white;
            border-radius: 5px;
            cursor: pointer;
        }
        input {
            margin-bottom: 15px;
        }
        .result {
            text-align: left;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="card">
        <h2>Digital Declutter Assistant</h2>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="file" required><br>
            <button type="submit">Analyze</button>
        </form>
        <div class="result">
            {{ result|safe }}
        </div>
    </div>
</body>
</html>
"""

def get_file_hash(filepath):
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        hasher.update(f.read())
    return hasher.hexdigest()

@app.route('/', methods=['GET', 'POST'])
def upload():
    result = ""
    if request.method == 'POST':
        file = request.files['file']
        if file:
            os.makedirs("uploads", exist_ok=True)
            zip_path = os.path.join("uploads", file.filename)
            file.save(zip_path)

            extract_path = os.path.join("uploads", "extracted")
            os.makedirs(extract_path, exist_ok=True)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)

            total_files = 0
            total_size = 0
            largest_file = ("", 0)
            hashes = {}
            duplicates = 0
            large_files = 0
            old_files = 0

            six_months_ago = datetime.now().timestamp() - (6 * 30 * 24 * 60 * 60)

            for root, dirs, files in os.walk(extract_path):
                for name in files:
                    total_files += 1
                    filepath = os.path.join(root, name)
                    size = os.path.getsize(filepath)
                    total_size += size

                    if size > largest_file[1]:
                        largest_file = (name, size)

                    if size > 50 * 1024 * 1024:
                        large_files += 1

                    last_modified = os.path.getmtime(filepath)
                    if last_modified < six_months_ago:
                        old_files += 1

                    file_hash = get_file_hash(filepath)
                    if file_hash in hashes:
                        duplicates += 1
                    else:
                        hashes[file_hash] = name

            clutter_score = min(100, duplicates * 5 + large_files * 3 + old_files * 2)

            result = f"""
            <h3>Analysis Result</h3>
            <p><strong>Total Files:</strong> {total_files}</p>
            <p><strong>Total Size:</strong> {round(total_size/1024/1024,2)} MB</p>
            <p><strong>Largest File:</strong> {largest_file[0]}</p>
            <p><strong>Duplicate Files:</strong> {duplicates}</p>
            <p><strong>Large Files (>50MB):</strong> {large_files}</p>
            <p><strong>Old Files (>6 months):</strong> {old_files}</p>
            <hr>
            <p><strong>Clutter Score:</strong> {clutter_score}/100</p>
            """

    return render_template_string(HTML, result=result)

if __name__ == '__main__':
    app.run(debug=True)
