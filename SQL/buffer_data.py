import json
import os
from datetime import datetime
from SQL.model import Experiment

BUFFER_FILE = "experiment_buffer.jsonl"

def save_experiment_to_buffer(exp: Experiment):
    """Append experiment data to local buffer file."""
    data = {
        "gen_at": exp.gen_at,
        "exp_id": exp.exp_id,
        "req_id": exp.req_id,
        "server_in": exp.server_in if exp.server_in else None,
        "server_out": exp.server_out if exp.server_out else None,
        "model_in": exp.model_in.isoformat() if exp.model_in else None,
        "model_out": exp.model_out.isoformat() if exp.model_out else None,
        "db_in": exp.db_in if exp.db_in else None,
        "db_out": exp.db_out if exp.db_out else None,
        "minio_in": exp.minio_in if exp.minio_in else None,
        "minio_out": exp.minio_out if exp.minio_out else None,
        "dpse_in": exp.dpse_in if exp.dpse_in else None,
        "dpse_out": exp.dpse_out if exp.dpse_out else None,
        "device": exp.device if exp.device else None,
        "gpu_usage": exp.gpu_usage if exp.gpu_usage else None,
        "cpu_usage": exp.cpu_usage,
        "memory_usage": exp.memory_usage,
        "process_count": exp.process_count,
        "fps": exp.fps,
    }
    with open(BUFFER_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n")


def load_buffered_experiments():
    """Read all experiments from buffer file."""
    if not os.path.exists(BUFFER_FILE):
        return []
    with open(BUFFER_FILE, "r", encoding="utf-8") as f:
        return [json.loads(line.strip()) for line in f if line.strip()]


def clear_buffer():
    """Remove buffer file after pushing to SQL."""
    if os.path.exists(BUFFER_FILE):
        os.remove(BUFFER_FILE)
