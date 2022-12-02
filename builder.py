import subprocess
import sys
import yaml
import tempfile
import shutil
import os
import json

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


def main():
    temp_dir = tempfile.mkdtemp()
    print(temp_dir)

    with open("asyncapi.yml", "r") as fp:
        data = yaml.load(fp, Loader)

    for klass in data["components"]["messages"]:
        with open(os.path.join(temp_dir, f"{klass}.json"), "w") as fp2:
            json.dump(data["components"]["messages"][klass]["payload"], fp2, indent=4)

        subprocess.run(
            [
                "datamodel-codegen",
                "--input",
                os.path.join(temp_dir, f"{klass}.json"),
                "--output",
                f"models/{klass}.py",
                "--field-constraints", # avoid illegal expression error
                "--use-default", # allow the use of default values
                "--class-name",
                klass,
            ]
        )

    shutil.rmtree(temp_dir)


if __name__ == "__main__":
    main()
