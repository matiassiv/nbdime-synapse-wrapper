import argparse
import json
import os
import tempfile

from git import Repo
from nbdime.webapp.nbdiffweb import main


def build_arg_parser():
    parser = argparse.ArgumentParser(
        prog="Synapse notebook diff tool",
        description="Git diffs of Synapse notebooks via a wrapper script for the nbdiff-web program",
    )

    parser.add_argument(
        "commit_a",
        nargs="?",
        default="HEAD",
        type=str,
        help="Reference to commit to diff from. Defaults to HEAD if nothing is provided",
    )
    parser.add_argument("commit_b", type=str, help="Reference to commit")

    parser.add_argument(
        "--repo_path",
        required=False,
        default=os.curdir,
        help="Optionally provide path to repo to diff from. Current directory or first parent directory that is a repo is default.",
    )

    # TODO add option to parse flags for underlying nbdiff tool
    return parser


# Function to read the contents of a file from a given commit
def read_file_from_commit(commit, file_path):
    try:
        # Get the blob for the file_path at the given commit
        blob = commit.tree / file_path
        # Return the contents of the file as a string
        return blob.data_stream.read().decode("utf-8")
    except KeyError:
        # The file does not exist in this commit
        return None


def read_and_validate_synapse_notebook(json_str: str) -> dict:
    try:
        nb = json.loads(json_str)
        # Check if expected keys exist in the synapse notebook, and that we do not read some random json
        if "properties" not in nb and "nbformat" not in nb:
            return None
        return nb
    except json.JSONDecodeError:
        print("JSON file could not be read")
        print(json_str)


def convert_synapse_notebook_to_jupyter(synapse_nb: dict) -> dict:
    # TODO make this more robust and cross-check with jupyter format
    jupyter_compatible = dict()

    jupyter_compatible["metadata"] = synapse_nb["properties"]["metadata"]
    jupyter_compatible["nbformat"] = synapse_nb["properties"]["nbformat"]
    jupyter_compatible["nbformat_minor"] = synapse_nb["properties"]["nbformat_minor"]
    jupyter_compatible["cells"] = synapse_nb["properties"]["cells"]

    for cell in jupyter_compatible["cells"]:
        if "metadata" not in cell:
            cell["metadata"] = {}
        if "outputs" not in cell and cell["cell_type"] == "code":
            cell["outputs"] = []

    return jupyter_compatible


def get_diffable_notebooks(repo, commit_a, commit_b):
    # Get the diff between the two commit refs/branches
    diff_index = repo.commit(commit_a).diff(commit_b, create_patch=True)
    for diff_item in diff_index:
        notebook_a = None
        # Check that file exists and that it is a .json file (Synapse notebook extension)
        if diff_item.a_path is not None and diff_item.a_path.endswith(".json"):
            file_a = read_file_from_commit(repo.commit(commit_a), diff_item.a_path)
            synapse_nb = read_and_validate_synapse_notebook(file_a)
            notebook_a = {
                "path": diff_item.a_path,
                "notebook": convert_synapse_notebook_to_jupyter(synapse_nb),
            }

        notebook_b = None
        # Check that file exists and that it is a .json file (Synapse notebook extension)
        if diff_item.a_path is not None and diff_item.a_path.endswith(".json"):
            file_b = read_file_from_commit(repo.commit(commit_b), diff_item.a_path)
            synapse_nb = read_and_validate_synapse_notebook(file_b)
            notebook_b = {
                "path": diff_item.b_path,
                "notebook": convert_synapse_notebook_to_jupyter(synapse_nb),
            }

        # If none of the files are synapse notebooks, we jump to the next diff item pair
        if notebook_a is None and notebook_b is None:
            continue

        yield (notebook_a, notebook_b)


def create_temp_file_with_name(directory, prefix, nb_dict):
    if nb_dict is None:
        return None

    # Temporary folder cannot write to files nested within a subfolder, so we artificially flatten the file path
    nb_filename = prefix + nb_dict["path"].replace("/", "_")
    temp_file_path = os.path.join(directory, nb_filename)
    with open(temp_file_path, "w") as temp_file:
        # You can write initial content to the file if needed
        temp_file.write(json.dumps(nb_dict["notebook"]))
    return temp_file_path


if __name__ == "__main__":
    parser = build_arg_parser()
    args, unknowns = parser.parse_known_args()

    repo_path = os.path.abspath(args.repo_path)
    repo = Repo(repo_path, search_parent_directories=True)
    assert not repo.bare

    for notebook_a, notebook_b in get_diffable_notebooks(
        repo, args.commit_a, args.commit_b
    ):
        # Create a temporary directory
        with tempfile.TemporaryDirectory(dir=".") as temp_dir:
            # Create two temporary files with specific names
            temp_file1_path = create_temp_file_with_name(
                temp_dir, args.commit_a, notebook_a
            )
            temp_file2_path = create_temp_file_with_name(
                temp_dir, args.commit_b, notebook_b
            )

            # Paths of the temporary files
            main([temp_file1_path, temp_file2_path, *unknowns])
