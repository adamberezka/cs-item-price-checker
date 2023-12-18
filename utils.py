import time


def log_invocation(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        print(f"Function: {func.__name__}")
        print(f"Arguments: args={args}, kwargs={kwargs}")
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"\nFunction '{func.__name__}' took {execution_time:.6f} seconds.\n")
        print()
        return result
    return wrapper
