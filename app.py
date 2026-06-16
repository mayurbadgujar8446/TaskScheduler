# pyrefly: ignore [missing-import]
from flask import Flask, request, jsonify, send_from_directory
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


def calculate_available_time(work_start, work_end, breaks):
    def to_min(t):
        h, m = map(int, t.split(":"))
        return h * 60 + m

    total = to_min(work_end) - to_min(work_start)
    brk_min = 0
    for b in breaks:
        bs = max(to_min(b["start"]), to_min(work_start))
        be = min(to_min(b["end"]), to_min(work_end))
        if be > bs:
            brk_min += (be - bs)
    return max((total - brk_min) / 60.0, 0)


@app.route("/optimize/greedy", methods=["POST"])
def optimize_greedy():
    data = request.get_json()
    tasks = data.get("tasks", [])
    available = calculate_available_time(
        data.get("work_start", "08:00"),
        data.get("work_end", "18:00"),
        data.get("breaks", [])
    )

    sorted_tasks = sorted(tasks, key=lambda t: t["time"])
    selected = []
    time_used = 0.0
    priority_sum = 0

    for task in sorted_tasks:
        if time_used + task["time"] <= available:
            selected.append(task)
            time_used += task["time"]
            priority_sum += task["priority"]

    return jsonify({
        "algorithm": "Greedy (Shortest Job First)",
        "available_time": round(available, 2),
        "selected_tasks": selected,
        "total_time_used": round(time_used, 2),
        "total_priority": priority_sum,
        "tasks_completed": len(selected)
    })


@app.route("/optimize/dp", methods=["POST"])
def optimize_dp():
    data = request.get_json()
    tasks = data.get("tasks", [])
    available = calculate_available_time(
        data.get("work_start", "08:00"),
        data.get("work_end", "18:00"),
        data.get("breaks", [])
    )

    capacity = int(available * 60)
    n = len(tasks)

    if n == 0 or capacity <= 0:
        return jsonify({
            "algorithm": "Dynamic Programming (0/1 Knapsack)",
            "available_time": round(available, 2),
            "selected_tasks": [], "total_time_used": 0,
            "total_priority": 0, "tasks_completed": 0
        })

    weights = [int(t["time"] * 60) for t in tasks]
    values = [t["priority"] for t in tasks]

    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for w in range(capacity + 1):
            dp[i][w] = dp[i - 1][w]
            if weights[i - 1] <= w:
                dp[i][w] = max(dp[i][w], dp[i - 1][w - weights[i - 1]] + values[i - 1])

    selected = []
    w = capacity
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            selected.append(tasks[i - 1])
            w -= weights[i - 1]
    selected.reverse()

    time_used = sum(t["time"] for t in selected)
    priority_sum = sum(t["priority"] for t in selected)

    return jsonify({
        "algorithm": "Dynamic Programming (0/1 Knapsack)",
        "available_time": round(available, 2),
        "selected_tasks": selected,
        "total_time_used": round(time_used, 2),
        "total_priority": priority_sum,
        "tasks_completed": len(selected)
    })


@app.route("/", methods=["GET"])
def index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'index.html')


@app.route("/style.css", methods=["GET"])
def serve_css():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'style.css')


@app.route("/api/status", methods=["GET"])
def api_status():
    return jsonify({"status": "running", "service": "Smart Task Scheduler"})


if __name__ == "__main__":
    print("=" * 50)
    print("  Smart Task Scheduler - http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True, port=5000)
