import subprocess
import tempfile
import shutil
import os
import jsonref
import sys
import multiprocessing
import yaml
from typing import List, Tuple

THIS_DIR = os.path.abspath(os.path.dirname(__file__))


def process_message(temp_dir: str, message_data: dict, message_name) -> Tuple[List[str], List[str]]:
    print(f"Building {message_name}")

    # write the jsonschema for one message type
    with open(os.path.join(temp_dir, f"{message_name}.json"), "w") as fp:
        jsonref.dump(message_data[message_name]["payload"], fp, indent=4)

    # generate the code
    output = subprocess.check_output(
        [
            "datamodel-codegen",
            "--input",
            os.path.join(temp_dir, f"{message_name}.json"),
            "--class-name",
            message_name,
            "--field-constraints", # avoid illegal expression error
            "--use-field-description" # use docstrings
        ]
    ).decode("utf-8")

    output_lines = output.splitlines(keepends=False)
    # remove comment lines
    output_lines = [line for line in output_lines if not line.startswith("#")]

    # split output by import statements and class declarations
    for i, line in enumerate(output_lines):
        if line.startswith("class"):
            # return import lines, and class lines
            return output_lines[:i], output_lines[i:]

    # if this happens, parsing failed
    raise ValueError

def main():
    output_file = os.path.join(THIS_DIR, "models.py")

    # create a temp directory to save json files to
    temp_dir = tempfile.mkdtemp()

    # read in the api spec
    with open(os.path.join(THIS_DIR, "asyncapi.yml"), "r") as fp:
        # load the YML data
        raw_data = yaml.load(fp, yaml.CLoader)
        # convert to json so we can use jsonref
        data: dict = jsonref.replace_refs(raw_data) # type: ignore

    # process messages in multiprocessing, to make it faster
    message_data = data["components"]["messages"]

    with multiprocessing.Pool() as p:
        rs = p.starmap(process_message, [[temp_dir, message_data, message] for message in message_data])

    # unpack results
    import_code_lines = []
    model_code_lines = []
    for r in rs:
        import_code_lines.extend(r[0])
        model_code_lines.extend(r[1])

    # delete the temp directory
    shutil.rmtree(temp_dir)

    # once everything is generated, create one singular file
    with open(output_file, "w") as fp:
        fp.write("\n".join(import_code_lines))
        fp.write("\n".join(model_code_lines))

    subprocess.check_call([sys.executable, "-m", "black", output_file])
    subprocess.check_call([sys.executable, "-m", "isort", output_file])

    # npx ag asyncapi.yml @asyncapi/html-template --install --output output --force-write --param sidebarOrganization=hierarchical
    # PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

if __name__ == "__main__":
    main()
