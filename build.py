import subprocess
import tempfile
import shutil
import os
import jsonref
import sys

THIS_DIR = os.path.abspath(os.path.dirname(__file__))


def main():
    output_file = os.path.join(THIS_DIR, "models.py")

    # create a temp directory to save json files to
    temp_dir = tempfile.mkdtemp()

    # read in the api spec
    with open(os.path.join(THIS_DIR, "asyncapi.json"), "r") as fp:
        data: dict = jsonref.load(fp) # type: ignore

    # process messages
    import_code_lines = []
    model_code_lines = []

    messages = data["components"]["messages"]

    for message in messages:
        print(f"Building {message}")

        # write the jsonschema for one message type
        with open(os.path.join(temp_dir, f"{message}.json"), "w") as fp:
            jsonref.dump(messages[message]["payload"], fp, indent=4)

        # generate the code
        output = subprocess.check_output(
            [
                "datamodel-codegen",
                "--input",
                os.path.join(temp_dir, f"{message}.json"),
                "--class-name",
                message,
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
                import_code_lines.extend(output_lines[:i])
                model_code_lines.extend(output_lines[i:])
                break

    # delete the temp directory
    shutil.rmtree(temp_dir)

    # once everything is generated, create one singular file
    with open(output_file, "w") as fp:
        fp.write("\n".join(import_code_lines))
        fp.write("\n".join(model_code_lines))

    subprocess.check_call([sys.executable, "-m", "black", output_file])
    subprocess.check_call([sys.executable, "-m", "isort", output_file])


if __name__ == "__main__":
    main()
