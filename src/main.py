import yaml
from utils.github_api import fetch_repositories
from utils.log import log_message
from utils.file_handler import save_metadata, get_run_start_time, load_metadata

def load_config(config_file='config/config.yaml'):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config

def main():
    config = load_config()
    start_time = get_run_start_time(config)
    metadata = load_metadata(config['metadata']['file_name'])
    log_message(f'Starting crawling process: start_time: {start_time}', config['logging']['log_file'])
    
    # Fetch repositories and their details for each starting point
    for starting_point in config['crawl_targets']:
        fetch_repositories(starting_point,  config, metadata)
    
    # Save final metadata
    save_metadata(metadata, config)
    
    # Log the completion of the crawling process
    log_message('Crawling completed', config['logging']['log_file'])

if __name__ == '__main__':
    main()