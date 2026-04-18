from flask import Flask, request, jsonify
from models import db, User, Task
from config import Config
import jwt
import datetime
import sqlite3

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    db.create_all()

# @app.route("/")
# def index():
#     return jsonify({
#         "name": "Task API",
#         "version": "1.0.0",
#         "endpoints": {
#             "POST /login": "Authenticate and get a token",
#             "POST /tasks": "Create a new task",
#             "GET /tasks": "Get tasks by user_id"
#         },
#         "status": "running"
#     })

@app.route("/")
def index():
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Task API</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0d1117; color: #e6edf3; font-family: monospace; padding: 40px; transition: background 0.2s, color 0.2s; }
        body.light { background: #ffffff; color: #1f2328; }
        body.light .endpoints { border-color: #d0d7de; }
        body.light .endpoint { border-color: #d0d7de; }
        body.light .path { color: #1f2328; }
        body.light .version { color: #656d76; }
        body.light .desc { color: #656d76; }
        body.light .status { color: #656d76; }
        body.light .post { background: #dafbe1; color: #1a7f37; }
        body.light .get { background: #ddf4ff; color: #0969da; }
        .toggle { position: absolute; top: 32px; right: 40px; background: none; border: 1px solid #30363d; color: #8b949e; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-family: monospace; font-size: 12px; }
        body.light .toggle { border-color: #d0d7de; color: #656d76; }
        .container { max-width: 600px; margin: 60px auto; }
        .badge { display: inline-block; background: #238636; color: #fff; font-size: 11px; padding: 2px 8px; border-radius: 12px; margin-bottom: 16px; }
        h1 { font-size: 28px; font-weight: 600; margin-bottom: 8px; }
        .version { color: #8b949e; font-size: 13px; margin-bottom: 32px; }
        .endpoints { border: 1px solid #30363d; border-radius: 8px; overflow: hidden; }
        .endpoint { display: flex; align-items: center; gap: 12px; padding: 14px 18px; border-bottom: 1px solid #30363d; }
        .endpoint:last-child { border-bottom: none; }
        .method { font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 4px; min-width: 44px; text-align: center; }
        .post { background: #1f4a1f; color: #3fb950; }
        .get { background: #1a3a5c; color: #58a6ff; }
        .path { color: #e6edf3; font-size: 13px; flex: 1; }
        .desc { color: #8b949e; font-size: 12px; }
        .status { margin-top: 24px; color: #8b949e; font-size: 12px; }
        .dot { display: inline-block; width: 7px; height: 7px; background: #3fb950; border-radius: 50%; margin-right: 6px; }
    </style>
</head>
<body>
    <button class="toggle" id="themeBtn" onclick="toggleTheme()">☾ Dark</button>
    <div class="container">
        <span class="badge">v1.0.0</span>
        <h1>Task API</h1>
        <div class="version">A simple REST API with JWT authentication</div>
        <div class="endpoints">
            <div class="endpoint">
                <span class="method post">POST</span>
                <span class="path">/login</span>
                <span class="desc">Authenticate and get a token</span>
            </div>
            <div class="endpoint">
                <span class="method post">POST</span>
                <span class="path">/tasks</span>
                <span class="desc">Create a new task</span>
            </div>
            <div class="endpoint">
                <span class="method get">GET</span>
                <span class="path">/tasks</span>
                <span class="desc">Get tasks by user ID</span>
            </div>
        </div>
        <div class="status"><span class="dot"></span>Server running on http://127.0.0.1:5000</div>
    </div>
    <script>
        function toggleTheme() {
            const isLight = document.body.classList.toggle('light');
            document.getElementById('themeBtn').textContent = isLight ? '☀ Light' : '☾ Dark';
        }
    </script>
</body>
</html>
'''

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data["username"]).first()

    if user and user.password == data["password"]:
        token = jwt.encode(
            {"user_id": user.id, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
            app.config["SECRET_KEY"],
            algorithm="HS256",
        )
        return jsonify({"token": token})

    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/tasks", methods=["POST"])
def create_task():
    token = request.headers.get("Authorization")
    payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
    user_id = payload["user_id"]

    data = request.get_json()
    task = Task(title=data["title"], user_id=user_id)
    db.session.add(task)
    db.session.commit()
    return jsonify({"message": "Task created"}), 201


@app.route("/tasks", methods=["GET"])
def get_tasks():
    token = request.headers.get("Authorization")
    payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])

    requested_user_id = request.args.get("user_id")

    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM task WHERE user_id = {requested_user_id}")
    tasks = cursor.fetchall()
    conn.close()

    return jsonify({"tasks": tasks})


if __name__ == "__main__":
    app.run(debug=True)