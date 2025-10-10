import psycopg2
from psycopg2.extras import RealDictCursor
import uuid
from flask import Flask, request, jsonify, send_file
from dotenv import load_dotenv
import io
import base64
from agent import ask
from datetime import datetime, timedelta
import os
import json
import traceback


load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_PORT = os.getenv("DB_PORT") 

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        cursor_factory=RealDictCursor
    )
    return conn

def validate_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = cur.fetchone()
    if not user:
        
        cur.execute("INSERT INTO users (user_id) VALUES (%s)", (user_id,))
        conn.commit()
    cur.close()
    conn.close()

def create_session(user_id):
    session_id = str(uuid.uuid4())
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO sessions (session_id, user_id) VALUES (%s, %s)", (session_id, user_id))
    conn.commit()
    cur.close()
    conn.close()
    return session_id 

def save_message(session_id, user_text, ai_text):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        combined_message = {
            "ai": ai_text,
            "user": user_text
        }

        cur.execute("""
            INSERT INTO messages (session_id, message)
            VALUES (%s, %s)
        """, (session_id, json.dumps(combined_message)))

        cur.execute("""SELECT COUNT(*) AS cnt FROM messages WHERE session_id = %s""", (session_id,))
        count = cur.fetchone()["cnt"]
        if count == 1:
            cur.execute("""UPDATE sessions SET title = %s WHERE session_id = %s""", (user_text[:50], session_id))

        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        import traceback
        print("[save_message] Exception occurred:")
        traceback.print_exc()
        raise e

app = Flask(__name__)

@app.route("/query", methods=["POST"])
def query():
    try:
        # Step 1: Ensure user_id exists
        if not os.path.exists("user_id.txt"):
            user_id = str(uuid.uuid4())
            with open("user_id.txt", "w") as f:
                f.write(user_id)
        else:
            with open("user_id.txt", "r") as f:
                user_id = f.read().strip() 

        
        session_file = "session_id.txt"
        if not os.path.exists(session_file):
            session_id = create_session(user_id)
            with open(session_file, "w") as f:
                f.write(f"{session_id}|{datetime.utcnow().isoformat()}")
        else:
            with open(session_file, "r") as f:
                data = f.read().strip().split("|")
                session_id, timestamp = data[0], data[1]
                last_time = datetime.fromisoformat(timestamp)
                if datetime.utcnow() - last_time > timedelta(hours=24):
                    session_id = create_session(user_id)
                    with open(session_file, "w") as f:
                        f.write(f"{session_id}|{datetime.utcnow().isoformat()}")

        
        user_input = request.json.get("input", "").strip()
        if not user_input:
            return jsonify({"type": "error", "message": "Input cannot be empty"}), 400

        validate_user(user_id)

        
        include_file, file_content = False, ""
        with get_db_connection() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT filename, file_data, auto_use 
                FROM uploads WHERE session_id=%s 
                ORDER BY id DESC LIMIT 1
            """, (session_id,))
            upload = cur.fetchone()
            if upload:
                file_content = upload["file_data"].decode("utf-8", errors="ignore")
                include_file = upload["auto_use"] or "reference file" in user_input.lower()
                if upload["auto_use"]:
                    cur.execute("UPDATE uploads SET auto_use=FALSE WHERE session_id=%s AND filename=%s", (session_id, upload["filename"]))
                    conn.commit()

        if include_file:
            user_input = f"Reference file content:\n{file_content}\nUser Query: {user_input}"

        print(f" [query] Calling ask() with session_id={session_id} and input={user_input}")
        

        result = ask(user_input, session_id)

        if not result or not isinstance(result, dict):
            result = {"output": "I couldn’t generate a proper response this time."}

        output = result.get("output", "I couldn’t generate a proper response this time.")
        print(f" [query] ask() returned: {result}")


        
        save_message(session_id, user_input, output)

        
        if isinstance(output, str) and output.startswith("data:image/png;base64,"):
            image_data = output.split(",")[1]
            image_bytes = base64.b64decode(image_data)
            download = request.json.get("download", False)
            response = send_file(
                io.BytesIO(image_bytes),
                mimetype="image/png",
                as_attachment=download,
                download_name="generated.png"
            )
            response.headers["user_id"] = user_id
            response.headers["session_id"] = session_id
            return response

        
        return jsonify({
            "type": "text",
            "message": output,
            "user_id": user_id,
            "session_id": session_id
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"type": "error", "message": f"Server error: {type(e).__name__}: {str(e)}"}), 500


    
@app.route("/new_session", methods=["POST"])
def new_session():
        
    try:
        if not os.path.exists("user_id.txt"):
            user_id = str(uuid.uuid4())
            with open("user_id.txt", "w") as f:
                f.write(user_id)
        else:
            with open("user_id.txt", "r") as f:
                user_id = f.read().strip()

        session_id = create_session(user_id)
        with open("session_id.txt", "w") as f:
            f.write(f"{session_id}|{datetime.utcnow().isoformat()}")

        return jsonify({
            "message": "New session created successfully.",
            "session_id": session_id,
            "user_id": user_id
        })
    except Exception as e:
        return jsonify({"error": f"Failed to create new session: {str(e)}"}), 500
    
@app.route("/sessions", methods=["GET"])
def list_sessions():
    try:

        if not os.path.exists("user_id.txt"):
            return jsonify({"error": "User not initialized"}), 400

        with open("user_id.txt", "r") as f:
            user_id = f.read().strip()

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT session_id, start_time, end_time,
                COALESCE(title, 'New Chat') AS title,
                is_active
            FROM sessions
            WHERE user_id = %s
            ORDER BY start_time DESC
        """, (user_id,))
        sessions = cur.fetchall()
        cur.close(); conn.close()
        return jsonify(sessions)
    
    except Exception as e:
        return jsonify({"type": "error", "message": f"Server error: {str(e)}"}), 500
@app.route("/upload", methods=["POST"])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        if not file.filename:
            return jsonify({"error": "Empty filename"}), 400

        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        if size > 20 * 1024 * 1024:  # 20 MB limit
            return jsonify({"error": "File too large (max 20 MB)"}), 400

        if not os.path.exists("session_id.txt"):
            return jsonify({"error": "No active session found"}), 400

        with open("session_id.txt", "r") as f:
            session_id = f.read().strip().split("|")[0]

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO uploads (session_id, filename, file_data, content_type)
            VALUES (%s, %s, %s, %s)
        """, (session_id, file.filename, file.read(), file.content_type))
        conn.commit(); cur.close(); conn.close()

        return jsonify({"message": f"{file.filename} uploaded successfully", "session_id": session_id})
    except Exception as e:
        print(" [query] Exception occurred:")
        traceback.print_exc()  
        error_message = f"{type(e).__name__}: {str(e)}"
        return jsonify({"type": "error", "message": f"Server error: {error_message}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
