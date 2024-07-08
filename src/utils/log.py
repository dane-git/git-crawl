# src/utils/log.py
import datetime
import inspect
import os

def log_message(message, log_file, print_message=True):
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    frame = inspect.currentframe().f_back
    line_number = frame.f_lineno
    function_name = frame.f_code.co_name
    file_name = frame.f_code.co_filename
    log_entry = f'[{current_time}] {file_name}::{function_name} (line {line_number}): \n\t{message}'
    if print_message:
        print(message)
    
    if not os.path.exists(os.path.dirname(log_file)):
        os.makedirs(os.path.dirname(log_file))
    
    with open(log_file, 'a') as file:
        file.write(f'{log_entry}\n')
