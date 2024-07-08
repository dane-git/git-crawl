import yaml
from utils.github_api import fetch_repositories
from utils.log import log_message
from utils.file_handler import save_metadata, get_run_start_time

def load_config(config_file='config/config.yaml'):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config

def main():
    config = load_config()
    start_time = get_run_start_time(config)
    # print('config', config)
    print('start_time', start_time)
    # Log the start of the crawling process
    log_message(f'Starting crawling process: start_time: {start_time}', config['logging']['log_file'])
    
    # Fetch repositories and their details for each starting point
    for starting_point in config['crawl_targets']:
        fetch_repositories(starting_point, start_time, config)
    
    # Save final metadata
    save_metadata(config['metadata'], start_time, config)
    
    # Log the completion of the crawling process
    log_message('Crawling completed', config['logging']['log_file'])

if __name__ == '__main__':
    main()