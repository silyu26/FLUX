from SQL.crud import create_experiment_with_weather
from SQL.db import SessionLocal
from SQL.buffer_data import load_buffered_experiments, clear_buffer
from SQL.model import Experiment
from datetime import datetime

def push_buffer_to_db():
    """Push all buffered experiments to SQL and clear buffer."""
    experiments = load_buffered_experiments()
    if not experiments:
        print("No buffered experiments to push.")
        return

    with SessionLocal() as session:
        for exp_data in experiments:
            exp = Experiment(
                gen_at=exp_data["gen_at"],
                exp_id=exp_data["exp_id"],
                req_id=exp_data["req_id"],
                server_in=datetime.fromisoformat(exp_data["server_in"]) if exp_data["server_in"] else None,
                server_out=datetime.fromisoformat(exp_data["server_out"]) if exp_data["server_out"] else None,
                db_in=datetime.fromisoformat(exp_data["db_in"]) if exp_data["db_in"] else None,
                db_out=datetime.fromisoformat(exp_data["db_out"]) if exp_data["db_out"] else None,
                dpse_in=datetime.fromisoformat(exp_data["dpse_in"]) if exp_data["dpse_in"] else None,
                dpse_out=datetime.fromisoformat(exp_data["dpse_out"]) if exp_data["dpse_out"] else None,
                model_in=datetime.fromisoformat(exp_data["model_in"]),
                model_out=datetime.fromisoformat(exp_data["model_out"]),
                cpu_usage=exp_data["cpu_usage"],
                memory_usage=exp_data["memory_usage"],
                process_count=exp_data["process_count"],
                fps=exp_data["fps"]
            )
            create_experiment_with_weather(session, exp)

    clear_buffer()
    print(f"Pushed {len(experiments)} experiments to database.")

if __name__ == "__main__":
    push_buffer_to_db()