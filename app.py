import os
import uuid
from flask import Flask, request, jsonify, send_file
import io
import base64
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

        # Case 1: Image (base64)
        if isinstance(output, str) and output.startswith("data:image/png;base64,"):
            image_data = output.split(",")[1]  # remove "data:image/png;base64,"
            image_bytes = base64.b64decode(image_data)
            return send_file(
                io.BytesIO(image_bytes),
                mimetype="image/png",
                as_attachment=False,
                download_name="generated.png"
            )

        # Case 2: Text
        return jsonify({
            "type": "text",
            "message": output
        })

    except Exception as e:
        return jsonify({
            "type": "error",
            "message": f"Server error: {str(e)}"
        }), 500



if __name__ == "__main__":
    app.run(debug=True)
