import os
import uuid
from flask import Flask, request, jsonify, send_file, url_for
from agent import ask

app = Flask(__name__)

@app.route("/query", methods=["POST"])
def query():
    try:
        user_input = request.json.get("input", "").strip()
        if not user_input:
            return jsonify({"type": "error", "message": "Input cannot be empty"}), 400

        # Get agent response
        output = ask(user_input)

        # Check if output is an image path
        if isinstance(output, str) and output.startswith("generated_banners/"):
            filename = os.path.basename(output)
            download_url = url_for("download_image",filename=filename, _external=True)
            return jsonify({
                "type": "image",
                "message": "Image generated successfully",
                "download_url": download_url
            })

       
        return jsonify({
            "message": output
        })

    except Exception as e:
        return jsonify({
            "type": "error",
            "message": f"Server error: {str(e)}"
        }), 500

@app.route("/download/<filename>", methods=["GET"])
def download_image(filename):
    try:
        path = os.path.join("generated_banners", filename)
        if os.path.exists(path):
            return send_file(path, as_attachment=True)
        return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
