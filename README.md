# Synapse Notebook Diff Tool

This script provides a command-line interface to diff Synapse notebooks using the `nbdime`'s `nbdiff-web` tool. It is designed to work with Git repositories and allows users to visually compare changes between two commits.

## Prerequisites

Before using this tool, ensure that you have the following installed:

- Python 3
- nbdime (`nbdime`)
- GitPython (`gitpython`) *note: this is installed as part of nbdime*

You can install the required Python packages using `pip` (preferrably in a virtual environment of some kind):

```bash
pip install -r requirements.txt
```

**NOTE**:
I've encountered some issues using nbdiff-web version due to a misconfiguration for the webserver, which stops the server from starting. Several other users have reported the same issue, see here https://github.com/jupyter/nbdime/issues/749. To resolve this issue, downgrading the jupyter-server like so worked for me `pip install 'jupyter-server==2.12.5'`.

## Installation
To use the Synapse Notebook Diff Tool, you can clone or download this repository to your local machine. There is no need for a separate installation process as the script can be run directly from the command line.

## Usage
To use the tool, run the script as follows:

```bash
python path/to/synapse_notebook_diff.py <commit_a> <commit_b> [--repo_path]
```
Arguments:
- `commit_a`: Reference to the commit to diff from. Defaults to HEAD if nothing is provided.
- `commit_b`: Reference to the commit to compare against.
- `--repo_path`: Optionally provide the path to the repository to diff from. The default is the current directory or the first parent directory that is a repository. 

## Example
```bash
python synapse_notebook_diff.py HEAD~1 HEAD --repo_path /path/to/repo
```
This command will compare the Synapse notebooks between the last commit and the one before it in the repository located at `/path/to/repo`.

## How It Works
The script performs the following steps:

- Parses the command-line arguments to determine the commits to compare and the repository path.
- Initializes a Git repository object using the provided path.
- Retrieves the diff between the two commits for .json files, if they match the Synapse notebook format.
- Converts the Synapse notebooks to a Jupyter-compatible format.
- Creates temporary files for the converted notebooks. (The nbdiff-web tool expects files)
- Launches the nbdiff-web tool to visually display the diff between the notebooks.

## Limitations
The performed check on .json files to see if they are Synapse notebooks is quite rudimentary. Additionally, the conversion from Synapse to Jupyter format is basic and may not handle all cases.