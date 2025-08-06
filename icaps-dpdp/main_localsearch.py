import traceback

from src.utils.logging_engine     import logger
from algorithm.localsearch_solver import schedule

if __name__ == '__main__':
    try:
        schedule()
        print("SUCCESS")
    except Exception as e:
        logger.error("Failed to run algorithm")
        logger.error(f"Error: {e}, {traceback.format_exc()}")
        print("FAIL")
