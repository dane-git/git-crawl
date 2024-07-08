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

def fetch_url(url, headers, log_file):
    remaining, reset_time = check_rate_limit(headers, log_file)
    if remaining < 1:
        wait_time = reset_time - time.time()
        log_message(f'Rate limit reached. Waiting for {wait_time} seconds.', log_file)
        time.sleep(wait_time + 1)  # Add a buffer of 1 second
    response = requests.get(url, headers=headers)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        log_message(f'HTTPError: {e} for URL: {url}', log_file)
        return None
    return response.json()

def fetch_user_data(username, config):
    user_url = f"{config['github']['base_url']}/users/{username}"
    headers = {'Authorization': f"token {config['github']['token']}"}
    user_data = fetch_url(user_url, headers, config['logging']['log_file'])
    if user_data:
        user_info = {
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
        metadata["users"][username] = user_info
        if user_data.get('organizations_url'):
            fetch_organizations(user_data['organizations_url'], username, config)
    return user_data

def fetch_organizations(orgs_url, username, config):
    headers = {'Authorization': f"token {config['github']['token']}"}
    orgs_data = fetch_url(orgs_url, headers, config['logging']['log_file'])
    if orgs_data:
        for org in orgs_data:
            fetch_organization_data(org['login'], username, config)

def fetch_organization_data(org_login, username, config):
    org_url = f"{config['github']['base_url']}/orgs/{org_login}"
    headers = {'Authorization': f"token {config['github']['token']}"}
    org_data = fetch_url(org_url, headers, config['logging']['log_file'])
    if org_data:
        org_info = {
            'html_url': org_data.get('html_url'),
            'location': org_data.get('location'),
            'url': org_data.get('url'),
            'email': org_data.get('email'),
            'company': org_data.get('company'),
            'blog': org_data.get('blog'),
            'bio': org_data.get('bio'),
            'avatar_url': org_data.get('avatar_url'),
            'public_members_count': org_data.get('public_members_count'),
            'members_count': org_data.get('members_count'),
            'type': org_data.get('type')
        }
        metadata["organizations"][org_login] = org_info
        if username not in metadata["users"]:
            metadata["users"][username] = {}
        if "organizations" not in metadata["users"][username]:
            metadata["users"][username]["organizations"] = []
        metadata["users"][username]["organizations"].append(org_login)

def fetch_repositories(user_or_org, start_time, config):
    repos_url = f"{config['github']['base_url']}/users/{user_or_org}/repos"
    headers = {'Authorization': f"token {config['github']['token']}"}
    repos = fetch_url(repos_url, headers, config['logging']['log_file'])
    if repos is None:
        return []

    for repo in repos:
        repo_name = repo['name'].replace(' ', '_')
        if repo_name in config['repositories']['to_skip']:
            log_message(f'Skipping repository: {repo_name}', config['logging']['log_file'])
            continue
        repo_owner = repo['owner']['login']
        repo_owner_type = repo['owner']['type']
        log_message(f'Fetching repo: {repo_owner}/{repo_name}', config['logging']['log_file'])
        fetch_repo_details(repo_owner, repo_name, repo_owner_type, start_time, config)

def fetch_repo_details(owner, repo, owner_type, start_time, config):
    repo_url = f"{config['github']['base_url']}/repos/{owner}/{repo}"
    headers = {'Authorization': f"token {config['github']['token']}"}
    repo_data = fetch_url(repo_url, headers, config['logging']['log_file'])
    if repo_data is None:
        return

    branches_url = repo_url + '/branches'
    branches = fetch_url(branches_url, headers, config['logging']['log_file'])
    if branches is None:
        return

    forks_url = repo_url + '/forks'
    forks = fetch_url(forks_url, headers, config['logging']['log_file'])
    if forks is None:
        return

    forks_info = [{'owner': fork['owner']['login'], 'url': fork['html_url']} for fork in forks]

    commits_url = repo_url + '/commits'
    commits = fetch_url(commits_url, headers, config['logging']['log_file'])
    if commits is None:
        return

    commit_info = []
    for commit in commits:
        author_name = commit['commit']['author']['name']
        author_username = commit['author']['login'] if commit.get('author') else None
        if author_username and author_username not in metadata["users"]:
            fetch_user_data(author_username, config)
        commit_data = {
            'author': author_name,
            'author_username': author_username,
            'email': commit['commit']['author']['email'],
            'date': commit['commit']['author']['date'],
            'message': commit['commit']['message'],
            'sha': commit['sha'],
            'url': commit['html_url']
        }
        commit_info.append(commit_data)

    parent_info = {}
    if repo_data['fork']:
        parent_repo = repo_data['parent']
        parent_info = {
            'name': parent_repo['name'],
            'owner': parent_repo['owner']['login'],
            'url': parent_repo['html_url'],
            'clone_url': parent_repo.get('clone_url'),
            'created_at': parent_repo.get('created_at'),
            'description': parent_repo.get('description'),
            'html_url': parent_repo.get('html_url'),
            'homepage': parent_repo.get('homepage'),
            'updated_at': parent_repo.get('updated_at'),
            'topics': parent_repo.get('topics', []),
            'tags': parent_repo.get('tags', [])
        }

    repo_info = {
        'name': repo_data['name'],
        'owner': repo_data['owner']['login'],
        'owner_type': owner_type,
        'updated_at': repo_data['updated_at'],
        'branches': [branch['name'] for branch in branches],
        'forks': forks_info,
        'commits': commit_info,
        'parent': parent_info,
        'clone_url': repo_data.get('clone_url'),
        'created_at': repo_data.get('created_at'),
        'description': repo_data.get('description'),
        'html_url': repo_data.get('html_url'),
        'homepage': repo_data.get('homepage'),
        'updated_at': repo_data.get('updated_at'),
        'topics': repo_data.get('topics', []),
        'tags': repo_data.get('tags', [])
    }

    if owner_type == 'User' and owner not in metadata["users"]:
        fetch_user_data(owner, config)
    if owner_type == 'Organization' and owner not in metadata["organizations"]:
        fetch_organization_data(owner, owner, config)

    metadata["repositories"].append(repo_info)
    save_metadata(metadata, start_time, config)

    contents_url = f"{repo_url}/contents"
    fetch_contents(contents_url, repo_data['name'].replace(' ', '_'), repo_info, owner, config)

def fetch_contents(url, repo_name, repo_info, owner, config):
    headers = {'Authorization': f"token {config['github']['token']}"}
    contents = fetch_url(url, headers, config['logging']['log_file'])
    if contents is None:
        return

    for item in contents:
        if item['type'] == 'file' and item['name'].endswith(tuple(config['files']['supported_extensions'])):
            file_name = f'{owner}__{repo_name}__{item["path"].replace("/", "__")}'
            file_path = os.path.join(config['files']['download_directory'], file_name)
            print('item', item)
            download_file(item['download_url'], file_path, item['name'].endswith('.pdf'), item['name'].endswith('.mediawiki'), config)
            metadata["files"][file_name] = {
                'owner': repo_info['owner'],
                'url': item['html_url'],
                'update_dt': item['git_url']
            }
        elif item['type'] == 'dir':
            fetch_contents(item['url'], repo_name, repo_info, owner, config)
