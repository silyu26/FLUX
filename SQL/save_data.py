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
                acq_start = exp_data["acq_start"],
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
                minio_in=datetime.fromisoformat(exp_data["minio_in"]) if exp_data["minio_in"] else None,
                minio_out=datetime.fromisoformat(exp_data["minio_out"]) if exp_data["minio_out"] else None,
                cpu_usage=exp_data["cpu_usage"],
                memory_usage=exp_data["memory_usage"],
                process_count=exp_data["process_count"],
                fps=exp_data["fps"],
                device = exp_data["device"] if exp_data["device"] else None,
                gpu_usage = exp_data["gpu_usage"] if exp_data["gpu_usage"] else None,
                gpu_vram_usage = exp_data["gpu_vram_usage"] if exp_data["gpu_vram_usage"] else None,
                gpu_temperature = exp_data["gpu_temperature"] if exp_data["gpu_temperature"] else None,
                gpu_power = exp_data["gpu_power"] if exp_data["gpu_power"] else None
            )
            create_experiment_with_weather(session, exp)

    clear_buffer()
    print(f"Pushed {len(experiments)} experiments to database.")

if __name__ == "__main__":
    push_buffer_to_db()