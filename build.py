import subprocess
import tempfile
import shutil
import os
import jsonref
import sys
import yaml
import datamodel_code_generator
import pathlib

THIS_DIR = pathlib.Path(__file__).parent.absolute()


def main():
    output_file = THIS_DIR.joinpath("models.py")

    # create a temp directory to save json files to
    temp_dir = pathlib.Path(tempfile.mkdtemp())

    # read in the api spec
    with open(os.path.join(THIS_DIR, "asyncapi.yml"), "r") as fp:
        # load the YML data
        raw_data = yaml.load(fp, yaml.CLoader)
        # convert to json so we can use jsonref
        data: dict = jsonref.replace_refs(raw_data)  # type: ignore

    import_code_lines = []
    model_code_lines = []

    # process messages in multiprocessing, to make it faster
    messages_data = data["components"]["messages"]
    for message_name in messages_data:
        print(f"Building {message_name}")

        # temp file to save schema to
        message_schema_file = temp_dir.joinpath(f"{message_name}.json")
        message_output_file = temp_dir.joinpath(f"{message_name}model.py")

        # write the jsonschema for one message type
        with open(message_schema_file, "w") as fp:
            jsonref.dump(messages_data[message_name]["payload"], fp, indent=4)

        # generate the code
        datamodel_code_generator.generate(
            message_schema_file,
            class_name=message_name,
            field_constraints=True,
            use_field_description=True,
            output=message_output_file,
            input_file_type=datamodel_code_generator.InputFileType.JsonSchema,
        )
        output_lines = message_output_file.read_text().splitlines(keepends=False)

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

    # npx ag asyncapi.yml @asyncapi/html-template --install --output output --force-write --param sidebarOrganization=hierarchical
    # PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true


if __name__ == "__main__":
    main()
