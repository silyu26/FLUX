from sqlalchemy.orm import Session
from model import Experiment
from datetime import datetime

def create_experiment_with_weather(session: Session, exp: Experiment):
    try:
        session.add(exp)
        session.commit()
        session.refresh(exp)
        return exp
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()