import time
from services.database import initialize_database
from services.job_queue import worker_loop

if __name__ == "__main__":
    initialize_database()
    print("OnboardAI durable KYC worker started")
    worker_loop(1.0)
