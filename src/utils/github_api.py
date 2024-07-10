# src/utils/github_api.py
import requests
import time
from utils.log import log_message
from utils.rate_limiter import check_rate_limit
from utils.file_handler import download_file, save_metadata

import os

metadata = {
    "repositories": [],
    "users": {},
    "organizations": {},
    "files": {}
}

def fetch_url(url, headers, log_file, params=None):
    remaining, reset_time = check_rate_limit(headers, log_file)
    if remaining < 1:
        wait_time = reset_time - time.time()
        log_message(f'Rate limit reached. Waiting for {wait_time} seconds.', log_file)
        time.sleep(wait_time + 1)  # Add a buffer of 1 second
    response = requests.get(url, headers=headers, params=params)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        log_message(f'HTTPError: {e} for URL: {url}', log_file)
        return None
    return response.json()

def fetch_user_data(username, config, metadata):
    user_url = f"{config['github']['base_url']}/users/{username}"
    headers = {'Authorization': f"token {config['github']['token']}"}
    user_data = fetch_url(user_url, headers, config['logging']['log_file'])
    if user_data:
        metadata['users'][str(user_data['id'])] = { 
            'id': str(user_data['id']),
            'username': user_data['login'],
            'html_url': user_data.get('html_url'),
            'location': user_data.get('location'),
            'organizations_url': user_data.get('organizations_url'),
            'twitter_username': user_data.get('twitter_username'),
            'linkedin_username': user_data.get('linkedin_username'),
            'url': user_data.get('url'),
            'email': user_data.get('email'),
            'company': user_data.get('company'),
            'blog': user_data.get('blog'),
            'bio': user_data.get('bio'),
            'avatar_url': user_data.get('avatar_url'),
            'type': user_data.get('type')
        }
        log_message(f'Fetched User: {str(user_data["id"])}: {user_data["login"]}', config['logging']['log_file'])

def fetch_organization_data(org_name, config, metadata):
    org_url = f"{config['github']['base_url']}/orgs/{org_name}"
    headers = {'Authorization': f"token {config['github']['token']}"}
    org_data = fetch_url(org_url, headers, config['logging']['log_file'])


    if org_data:
        metadata['organizations'][str(org_data['id'])] = {
            'id': str(org_data['id']),
            'org_login': org_data['login'],
            'html_url': org_data.get('html_url'),
            'location': org_data.get('location'),
            'url': org_data.get('url'),
            'email': org_data.get('email'),
            'company': org_data.get('company'),
            'blog': org_data.get('blog'),
            'bio': org_data.get('bio'),
            'avatar_url': org_data.get('avatar_url'),
            'public_members_count': org_data.get('public_members_count',0),
            'members_count': org_data.get('members_count',0),
            'type': org_data.get('type')
        }
        log_message(f'Fetched User: {str(org_data["id"])}: {org_data["login"]}', config['logging']['log_file'])


def fetch_repositories(user_or_org, config, metadata):
    repos_url = f"{config['github']['base_url']}/users/{user_or_org}/repos"
    headers = {'Authorization': f"token {config['github']['token']}"}
    page = 1
    def filter_only_include_list(original_list, owner):
            print(96)
            print("owner", owner)
            print(original_list)
            _list = []
            for i in original_list:
                if '::' in i:
                    if i.split('::')[0] == owner:
                        _list.append(i.split('::')[1])
                else:
                    _list.append(i)
            print(106)
            print(_list)
            return _list
    while True:
        params = {'page': page, 'per_page': 100}
        repos = fetch_url(repos_url, headers, config['logging']['log_file'], params)
        if not repos:
            break
            
        for repo in repos:
            repo_id = repo['id']
            repo_name = repo['name'].replace(' ', '_')
            print(114, repo_name)
            only_include_list = []
            if 'only_include' in config['repositories']:
                only_include_list = filter_only_include_list(config['repositories']['only_include'], repo['owner']['login'])
                if repo_name not in only_include_list:
                    continue
            
            if repo_name in config['repositories']['to_skip']:
                log_message(f'Skipping repository: {repo_name}', config['logging']['log_file'])
                continue
            if str(repo_id) in metadata['repositories'] and repo['updated_at'] == metadata['repositories'][str(repo_id)]['updated_at']:
                log_message(f'Repository {repo["name"]} already processed, skipping.', config['logging']['log_file'])
                continue
            repo_owner = repo['owner']['login']
            log_message(f'Fetching repo: {repo_owner}/{repo_name}', config['logging']['log_file'])

            repo_info = get_repo_info(repo_id, repo, config, metadata)#, depth=1)
            metadata['repositories'][str(repo_id)] = repo_info
        page += 1 

def get_repo_info(repo_id, repo, config, metadata):
    repo_url = f"{config['github']['base_url']}/repos/{repo['owner']['login']}/{repo['name']}"
    headers = {'Authorization': f"token {config['github']['token']}"}
    repo_data = fetch_url(repo_url, headers, config['logging']['log_file'])
    if repo_data is None:
        return None
    
    owner_id = repo_data['owner']['id']
    if repo_data['owner']['type'] == 'User':
        if str(owner_id) not in metadata['users']:
            fetch_user_data(repo_data['owner']['login'], config, metadata)
    else:
        if str(owner_id) not in metadata['organizations']:
            fetch_organization_data(repo_data['owner']['login'], config, metadata)

    repo_info = {
        'id': repo_id,
        'name': repo_data['name'],
        'owner': repo_data['owner']['login'],
        'owner_id': owner_id,
        'owner_type': repo_data['owner']['type'],
        "forks_count": repo_data.get('forks_count'),
        "watchers_count": repo_data.get('watchers_count'),
        "subscribers_count": repo_data["subscribers_count"],
        "stargazers_count": repo_data.get("stargazers_count"),
        "language": repo_data.get("language"),
        "size": repo_data.get("size"),
        'updated_at': repo_data['updated_at'],
        'parent_id': repo_data['parent']['id'] if repo_data.get('parent') else None,
        'clone_url': repo_data['clone_url'],
        'created_at': repo_data['created_at'],
        'description': repo_data['description'],
        'html_url': repo_data['html_url'],
        'homepage': repo_data['homepage'],
        "license_key": repo_data.get('license').get('key'),
        "license_name": repo_data.get('license').get('name'),
        "license_url": repo_data.get('license').get('url'),
        'branches': [],
        'forks': [],
        'commits': [],
        'tags': [],
        'topics': repo_data.get('topics', [])
    }

    fetch_repo_details(repo_id, repo_info, config, metadata)

    # Fetch forks without diving into their details
    fetch_forks(repo_info, config, metadata)

    return repo_info

def fetch_forks(repo_info, config, metadata):
    repo_url = f"{config['github']['base_url']}/repos/{repo_info['owner']}/{repo_info['name']}/forks"
    headers = {'Authorization': f"token {config['github']['token']}"}
    page = 1
    while True:
        params = {'page': page, 'per_page': 100}
        forks = fetch_url(repo_url, headers, config['logging']['log_file'], params)
        if not forks:
            break
        for fork in forks:
            fork_id = fork['id']
            owner_id = fork['owner']['id']
            if fork['owner']['type'] == 'User':
                if str(owner_id) not in metadata['users']:
                    fetch_user_data(fork['owner']['login'], config, metadata)
            else:
                if str(owner_id) not in metadata['organizations']:
                    fetch_organization_data(fork['owner']['login'], config, metadata)

            fork_info = {
                'id': fork_id,
                'name': fork['name'],
                'owner': fork['owner']['login'],
                'owner_id': owner_id,
                'owner_type': fork['owner']['type'],
                'updated_at': fork['updated_at'],
                'parent_id': repo_info['id'],
                'clone_url': fork['clone_url'],
                'created_at': fork['created_at'],
                'description': fork['description'],
                'html_url': fork['html_url'],
                'homepage': fork['homepage'],
                'branches': [],
                'forks': [],
                'commits': [],
                'tags': [],
                'topics': fork.get('topics', [])
            }
            repo_info['forks'].append(fork_id)
            metadata['repositories'][str(fork_id)] = fork_info
        page += 1


def fetch_repo_details(repo_id, repo_info, config, metadata):
    repo_url = f"{config['github']['base_url']}/repos/{repo_info['owner']}/{repo_info['name']}"
    headers = {'Authorization': f"token {config['github']['token']}"}

    branches_url = repo_url + '/branches'
    branches = fetch_url(branches_url, headers, config['logging']['log_file'])
    if branches:
        for branch in branches:
            repo_info['branches'].append(branch['name'])

    commits_url = repo_url + '/commits'
    commits = fetch_url(commits_url, headers, config['logging']['log_file'])

    if commits:
        for commit in commits:
            # TODO sure this sha up, relate to repo i think
            commit_sha = commit['sha']
            author_id = commit['author']['id'] if commit['author'] else None

            if commit_sha not in repo_info['commits']:
                repo_info['commits'].append(commit_sha)
                metadata['commits'][commit_sha] = {
                    'id': commit['node_id'],
                    'repository_id': repo_id,
                    'node_id': commit['node_id'],
                    'owner_id': commit['author']['id'] if commit['author'] else None,
                    'author': commit['commit']['author']['name'],
                    'message': commit['commit']['message'],
                    'sha': commit_sha,
                    'url': commit['html_url'],
                    'date': commit['commit']['author']['date']
                }
                if author_id and str(author_id) not in metadata['users']:
                    fetch_user_data(commit['author']['login'], config, metadata)

    # Fetch and save file contents
    contents_url = f"{repo_url}/contents"
    fetch_contents(contents_url, repo_info, config, metadata)


def fetch_contents(url, repo_info, config, metadata):
    headers = {'Authorization': f"token {config['github']['token']}"}
    contents = fetch_url(url, headers, config['logging']['log_file'])
    if contents is None:
        return

    for item in contents:
        if item['type'] == 'file' and item['name'].endswith(tuple(config['files']['supported_extensions'])):
            file_sha = item['sha']
            if file_sha in metadata['files']:
                log_message(f'File {item["path"]} already processed, skipping.', config['logging']['log_file'])
                continue
            
            file_name = f"{repo_info['name'].replace(' ', '_')}__{item['path'].replace('/', '__')}"
            file_path = os.path.join(config['files']['download_directory'], file_name)
            download_file(item['download_url'], file_path, item['name'].endswith('.pdf'), item['name'].endswith('.mediawiki'), config)
            metadata['files'][file_sha] = {
                'repository_id': repo_info['id'],
                'save_name': file_name,
                'owner': repo_info['owner'],
                'url': item['html_url'],
                'blob': item['git_url'],
                'name': item['name'],
                'path': item['path'],
                'sha': file_sha,
                'size': item['size']
            }
        elif item['type'] == 'dir':
            fetch_contents(item['url'], repo_info, config, metadata)
