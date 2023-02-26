import argparse
import dataclasses
import json
import os
import pathlib
import shlex
import shutil
import subprocess
from typing import Dict, List, Optional

import jinja2
import jsonref
import yaml

try:
    import tomllib  # type: ignore
except ImportError:
    import tomli as tomllib  # type: ignore

THIS_DIR = pathlib.Path(__file__).parent
MQTT_DIR = THIS_DIR.joinpath("bell", "avr", "mqtt")


@dataclasses.dataclass
class PropertyTypeHint:
    prepend_lines: List[str]
    """
    Lines that should be prepended to the generated code.
    """
    type_checking: bool
    """
    If there is a seperate type hint if `TYPE_CHECKING` is true.
    """
    type_hint: str
    """
    The generated type hint.
    """
    type_checking_type_hint: Optional[str] = None
    """
    The generated type hint if `TYPE_CHECKING` is true.
    """
    core_type_hint: Optional[str] = None
    """
    The core variable type hint if in an array, such as an `int`.
    """
    validator: bool = False
    """
    If a validator is required.
    """


def create_name(parent: str, child: str) -> str:
    return (parent + child.title()).replace("_", "")


def type_hint_for_number_property(
    property_: Dict, name: str, parent_name: str, nested: bool = False
) -> PropertyTypeHint:
    """
    Take JSON schema data and turn it into a Python type hint for a number property.
    """
    # convert the jsonschema type to a python type
    if property_["type"] == "number":
        python_type = "float"
    elif property_["type"] == "integer":
        python_type = "int"
    else:
        raise ValueError(f"Not a valid number type: {property_['type']}")

    # if there are no extras, just return the python type
    if all(p not in property_ for p in ["default", "minimum", "maximum"]):
        return PropertyTypeHint(
            prepend_lines=[],
            type_checking=False,
            type_hint=python_type,
        )

    # otherwise, add a Field object, with a possible default
    # https://docs.pydantic.dev/visual_studio_code/#adding-a-default-with-field
    field_value = "..."
    default = property_.get("default", None)
    if default is not None:
        field_value = f"default={default}"

    output = f"{python_type} = Field({field_value}"

    # possible min value
    if "minimum" in property_:
        output += f", ge={property_['minimum']}"

    # possible max value
    if "maximum" in property_:
        output += f", le={property_['maximum']}"

    # round it out and return
    output += ")"

    # if we're nested and have constraints, return a child class
    if nested:
        subclass_name = f"{create_name(parent_name, name)}Item"
        return PropertyTypeHint(
            prepend_lines=[
                f"class {subclass_name}(BaseModel):",
                f"\t__root__: {output}",
                "",
                f"\tdef __{python_type}__(self) -> {python_type}:",
                "\t\treturn self.__root__",
                "",
                "",
            ],
            type_checking=True,
            type_hint=subclass_name,
            type_checking_type_hint=python_type,
            core_type_hint=python_type,
            validator=True,
        )

    # return computed type hint
    return PropertyTypeHint(
        prepend_lines=[],
        type_checking=False,
        type_hint=output,
    )


def type_hint_for_array_property(
    property_: Dict, name: str, parent_name: str, nested: bool = False
) -> PropertyTypeHint:
    """
    Take JSON schema data and turn it into a Python type hint for an array property.
    """
    sub_property_type_hint = type_hint_for_property(
        property_["items"],
        required=True,
        name=name,
        parent_name=parent_name,
        nested=True,
    )

    # basic type
    python_type = f"List[{sub_property_type_hint.type_hint}]"
    python_type_checking_type = (
        f"List[{sub_property_type_hint.type_checking_type_hint}]"
    )

    if (
        "minItems" in property_
        and "maxItems" in property_
        and property_["minItems"] == property_["maxItems"]
    ):
        # if there are a fixed number of items, use a Tuple
        python_type = f"Tuple[{', '.join([sub_property_type_hint.type_hint] * property_['minItems'])}]"
        python_type_checking_type = f"Tuple[{', '.join([sub_property_type_hint.type_checking_type_hint] * property_['minItems'])}]"

    if "minItems" not in property_ and "maxItems" not in property_:
        # if just a basic list and nothing else, return
        return PropertyTypeHint(
            prepend_lines=sub_property_type_hint.prepend_lines,
            type_checking=False,
            type_hint=python_type,
        )

    # otherwise, add a Field object
    output = f"{python_type} = Field(..."
    if sub_property_type_hint.type_checking:
        output = f"conlist({sub_property_type_hint.type_hint}"

    # possible min value
    if "minItems" in property_:
        output += f", min_items={property_['minItems']}"

    # possible max value
    if "maxItems" in property_:
        output += f", max_items={property_['maxItems']}"

    # round it out and return
    output += ")"

    return PropertyTypeHint(
        prepend_lines=sub_property_type_hint.prepend_lines,
        type_checking=sub_property_type_hint.type_checking,
        type_hint=output,
        type_checking_type_hint=python_type_checking_type,
        core_type_hint=sub_property_type_hint.core_type_hint,
        validator=True,
    )


def type_hint_for_property(
    property_: Dict, required: bool, name: str, parent_name: str, nested: bool = False
) -> PropertyTypeHint:
    """
    Given property data, return the type hint for a property, plus a
    possible list of extra lines that need to be added before the parent class.
    """
    property_type_hint = PropertyTypeHint(
        prepend_lines=[], type_checking=False, type_checking_type_hint="", type_hint=""
    )

    if property_["type"] == "string":
        if "enum" in property_:
            property_type_hint.type_hint = (
                'Literal["' + '", "'.join(property_["enum"]) + '"]'
            )
        else:
            property_type_hint.type_hint = "str"

    elif property_["type"] in ["number", "integer"]:
        subclass_name = (parent_name + name.title()).replace("_", "")
        property_type_hint = type_hint_for_number_property(
            property_, nested=nested, name=name, parent_name=parent_name
        )

    elif property_["type"] == "boolean":
        property_type_hint.type_hint = "bool"

    elif property_["type"] == "object":
        subclass_name = create_name(parent_name, name)
        (
            property_type_hint.type_hint,
            property_type_hint.prepend_lines,
        ) = subclass_name, build_class_code(subclass_name, property_)

    elif property_["type"] == "array":
        property_type_hint = type_hint_for_array_property(
            property_, name, parent_name, nested=nested
        )

    else:
        raise ValueError(f'Cannot handle type: {property_["type"]}')

    if not required and "Field(default=" not in property_type_hint.type_hint:
        # if something has a default, don't actually use Optional[]
        if "=" in property_type_hint.type_hint:
            # in case the type hint has something it's equal to like a field
            chunks = property_type_hint.type_hint.split(" =", maxsplit=1)
            property_type_hint.type_hint = f"Optional[{chunks[0]}] = {chunks[1]}"
        else:
            property_type_hint.type_hint = f"Optional[{property_type_hint.type_hint}]"

    return property_type_hint


def build_class_code(class_name: str, class_data: dict) -> List[str]:
    assert class_data["type"] == "object"
    assert class_data["additionalProperties"] is False

    output_lines = [
        f"class {class_name}(BaseModel):",
    ]

    if "properties" in class_data:
        for property_name in class_data["properties"]:
            property_ = class_data["properties"][property_name]

            # compute the type hint
            property_type_hint = type_hint_for_property(
                property_,
                required=property_name in class_data["required"],
                name=property_name,
                parent_name=class_name,
            )

            # add extra lines first
            output_lines = property_type_hint.prepend_lines + output_lines

            # add the type hint
            if property_type_hint.type_checking:
                output_lines.append("\tif TYPE_CHECKING:")
                output_lines.append(
                    f"\t\t{property_name}: {property_type_hint.type_checking_type_hint}"
                )
                output_lines.append("\telse:")
                output_lines.append(
                    f"\t\t{property_name}: {property_type_hint.type_hint}"
                )
            else:
                output_lines.append(
                    f"\t{property_name}: {property_type_hint.type_hint}"
                )

            # add a docstring if there is one
            if "description" in property_:
                output_lines.extend(['\t"""', "\t" + property_["description"], '\t"""'])

            if property_type_hint.validator:
                output_lines.extend(
                    [
                        f"\t@validator('{property_name}')",
                        f"\tdef validate_{property_name}(cls, v):",
                        f"\t\treturn _convert_type(v, {property_type_hint.core_type_hint})",
                        "",
                    ]
                )
    else:
        output_lines.append("\tpass")

    # add a blank line at the end
    output_lines.append("")
    return output_lines


def python_code() -> None:
    output_file = MQTT_DIR.joinpath("payloads.py")

    # read in the api spec
    with open(MQTT_DIR.joinpath("asyncapi.yml"), "r") as fp:
        # load the YML data
        raw_asyncapi_data = yaml.load(fp, yaml.CLoader)
        # convert to json so we can use jsonref
        asyncapi_data: dict = jsonref.replace_refs(raw_asyncapi_data)  # type: ignore

    # first, build a dict of topics to class names
    topic_class: Dict[str, str] = {}

    channels = raw_asyncapi_data["channels"]
    for topic in channels:
        # knab channel data
        channel = channels[topic]

        # make sure there is a publish or subscribe key underneath
        if "subscribe" in channel:
            topic_message = channel["subscribe"]
        elif "publish" in channel:
            topic_message = channel["publish"]
        else:
            raise ValueError(f"Publish or subscribe not found in channel {topic}")

        # parse out the class name
        topic_class[topic] = topic_message["message"]["$ref"].split("/")[-1]

    # now, build the class for each topic
    final_output_lines = [
        "# This file is automatically @generated. DO NOT EDIT!",
        "# fmt: off",
        "",
        "from __future__ import annotations",
        "",
        "from typing import TYPE_CHECKING, Any, List, Literal, Optional, Protocol, Tuple, Type, Union",
        "",
        "from pydantic import BaseModel as PydanticBaseModel",
        "from pydantic import Extra, Field, conlist, validator",
        "",
        "",
        "def _convert_type(iter: Union[list, tuple], convert_to: Union[Type[int], Type[float]]) -> Union[tuple, int, float]:",
        "\tif isinstance(iter, (tuple, list)):",
        "\t\treturn tuple(_convert_type(x, convert_to) for x in iter)",
        "\telse:",
        "\t\treturn convert_to(iter)",
        "",
        "",
        "class BaseModel(PydanticBaseModel):",
        "\tclass Config:",
        "\t\textra = Extra.forbid",
        "",
        "",
    ]

    messages = asyncapi_data["components"]["messages"]
    for message in messages:
        print(f"Building code for {message}")
        final_output_lines.extend(
            build_class_code(message, messages[message]["payload"])
        )

    # generate callables
    for klass in set(topic_class.values()):
        args = f", payload: {klass}"
        if "EmptyMessage" in klass:
            args = ""

        final_output_lines.extend(
            (
                f"class _{klass}Callable(Protocol):",
                '\t"""',
                "\tClass used only for type-hinting MQTT callbacks.",
                '\t"""',
                f"\tdef __call__(self{args}) -> Any:",
                "\t\t...",
                "",
            )
        )

    # convert tabs to spaces
    final_output_lines = [i.replace("\t", "    ") for i in final_output_lines]

    # write out file
    with open(output_file, "w") as fp:
        fp.write("\n".join(final_output_lines))

    # run jinja templates
    template_loader = jinja2.FileSystemLoader(searchpath=MQTT_DIR)
    template_env = jinja2.Environment(loader=template_loader)

    # for each file ending in .j2, render and write a .py file
    for template in MQTT_DIR.glob("*.j2"):
        print("Rendering", template)
        with open(MQTT_DIR.joinpath(template.name.replace(".j2", ".py")), "w") as fp:
            fp.write(
                template_env.get_template(template.name).render(
                    topic_class=topic_class,
                )
            )


def docs() -> None:
    # create docs dir
    docs_dir = THIS_DIR.joinpath("docs")
    docs_dir.mkdir(parents=True, exist_ok=True)

    apispec = MQTT_DIR.joinpath("asyncapi.yml")

    with open(THIS_DIR.joinpath("pyproject.toml"), "rb") as fp:
        pyproject = tomllib.load(fp)

    # required for Windows because `npx` is a cmd script
    npx = shutil.which("npx")
    assert npx is not None

    cmd = [
        npx,
        "ag",  # asyncapi generator
        str(apispec.absolute()),  # asyncapi spec
        "@asyncapi/html-template",  # html template
        "--output",
        str(docs_dir.absolute()),  # output directory
        "--force-write",  # force overwrite
        "--param",
        f'version={pyproject["tool"]["poetry"]["version"]}',  # version
        "--param",
        "favicon=https://raw.githubusercontent.com/bellflight/AVR-Docs/main/static/favicons/android-chrome-512x512.png",
        "--param",
        f"config={json.dumps({'expand': {'messageExamples': True}})}",
    ]

    print("Building docs")
    print(shlex.join(cmd))

    subprocess.check_call(
        cmd,
        env={**os.environ, "PUPPETEER_SKIP_CHROMIUM_DOWNLOAD": "true"},
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs", action="store_true", help="Fenerate documentation")
    args = parser.parse_args()

    python_code()
    if args.docs:
        docs()
