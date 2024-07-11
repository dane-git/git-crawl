# git-crawler

## Overview

The GitHub Crawler is a Python script designed to fetch and process repository data from GitHub. It handles rate limiting, converts specific file formats, and logs detailed information about the crawling process. 

## Features

- Fetch repository details, including commits, branches, forks, and more.
- Skip specified repositories by name.
- Convert `.pdf` and `.mediawiki` files to Markdown.

- Handle GitHub API rate limiting.
- Log detailed messages with timestamps, file names, function names, and line numbers.
- Save metadata to a single file.  Goal to prevent duplicate api calls.

## Prerequisites

- Python 3.x
- GitHub personal access token
- Required Python libraries: `requests`, `fitz` (PyMuPDF), `markdownify`, `mwparserfromhell`, `pypandoc`

## Installation

### Install Python Libraries

```sh
pip install .
```

### install Pandoc
#### mac os
```sh
brew install pandoc
```

#### ubuntu/debian
```sh
sudo apt-get install pandoc
```

## Usage

1. Set up your GitHub personal access token:
Replace your_github_token_here with your actual GitHub personal access token in the script.

2. Specify Repositories configuration in `config/config.yaml`.   
See `example_config.yaml`.  

3. Run the Script:
Run the script to fetch and process repository data from the specified users and organizations.


## License
This project is licensed under the MIT License. See the LICENSE file for details.



## Documentation

- [TODO](TODO.md)
- [Notes](NOTES.md)
- [Scope](SCOPE.md)