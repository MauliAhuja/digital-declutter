from flask import Flask, request, render_template
import os
import hashlib
from collections import defaultdict

app = Flask(__name__)

# safety limit for Render free plan
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":

        files = request.files.getlist("files")
        file_data = []

        for file in files:
            if file.filename == "":
                continue

            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)

            size = os.path.getsize(filepath)

            with open(filepath, "rb") as f:
                file_hash = hashlib.md5(f.read()).hexdigest()

            file_data.append({
                "name": file.filename,
                "size": size,
                "hash": file_hash
            })

        total_size = sum(f["size"] for f in file_data)

        # Duplicate detection
        hash_map = defaultdict(list)
        for f in file_data:
            hash_map[f["hash"]].append(f)

        duplicates = [group for group in hash_map.values() if len(group) > 1]

        duplicate_count = sum(len(group) - 1 for group in duplicates)
        duplicate_waste = sum((len(group) - 1) * group[0]["size"] for group in duplicates)

        # Largest files
        largest = sorted(file_data, key=lambda x: x["size"], reverse=True)[:10]
        top_total = sum(f["size"] for f in largest)
        percentage = (top_total / total_size * 100) if total_size else 0

        # Screenshot detection
        screenshots = [
            f for f in file_data
            if "screenshot" in f["name"].lower()
        ]

        return render_template(
            "index.html",
            duplicate_count=duplicate_count,
            duplicate_waste=round(duplicate_waste / (1024*1024), 2),
            percentage=round(percentage, 2),
            screenshot_count=len(screenshots)
        )

    return render_template("index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)