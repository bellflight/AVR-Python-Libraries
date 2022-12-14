import pathlib
from typing import Dict, List, Tuple

import jsonref
import yaml

THIS_DIR = pathlib.Path(__file__).parent


def type_hint_for_number_property(property_: Dict, nested: bool = False) -> str:
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
        return python_type

    if nested:
        # if we're nested, return
        return python_type

    # otherwise, add a Field object, with a possible default
    output = f"{python_type} = Field({property_.get('default', '...')}"

    # possible min value
    if "minimum" in property_:
        output += f", ge={property_['minimum']}"

    # possible max value
    if "maximum" in property_:
        output += f", le={property_['maximum']}"

    # round it out and return
    output += ")"
    return output


def type_hint_for_array_property(
    property_: Dict, name: str, parent_name: str, nested: bool = False
) -> Tuple[str, List[str]]:
    """
    Take JSON schema data and turn it into a Python type hint for an array property.
    """
    subtype_hint, output_lines = type_hint_for_property(
        property_["items"], True, name, parent_name, True
    )

    # basic type
    python_type = f"List[{subtype_hint}]"

    if (
        "minItems" in property_
        and "maxItems" in property_
        and property_["minItems"] == property_["maxItems"]
    ):
        # if there are a fixed number of items, use a Tuple
        python_type = f"Tuple[{', '.join([subtype_hint] * property_['minItems'])}]"

    if "minItems" not in property_ and "maxItems" not in property_:
        # if just a basic list and nothing else, return
        return python_type, output_lines

    if nested:
        # if we're nested, return
        return python_type, output_lines

    # otherwise, add a Field object
    output = f"{python_type} = Field(..."

    # possible min value
    if "minItems" in property_:
        output += f", min_items={property_['minItems']}"

    # possible max value
    if "maxItems" in property_:
        output += f", max_items={property_['maxItems']}"

    # round it out and return
    output += ")"
    return output, output_lines


def type_hint_for_property(
    property_: Dict, required: bool, name: str, parent_name: str, nested: bool = False
) -> Tuple[str, List[str]]:
    """
    Given property data, return the type hint for a property, plus a
    possible list of extra lines that need to be added before the parent class.
    """
    output_lines = []

    if property_["type"] == "string":
        if "enum" in property_:
            type_hint = 'Literal["' + '", "'.join(property_["enum"]) + '"]'
        else:
            type_hint = "str"
    elif property_["type"] in ["number", "integer"]:
        type_hint = type_hint_for_number_property(property_, nested=nested)
    elif property_["type"] == "boolean":
        type_hint = "bool"
    elif property_["type"] == "object":
        subclass_name = parent_name + name.title()
        type_hint, output_lines = subclass_name, build_class_code(
            subclass_name, property_
        )
    elif property_["type"] == "array":
        type_hint, output_lines = type_hint_for_array_property(
            property_, name, parent_name, nested=nested
        )
    else:
        raise ValueError(f'Cannot handle type: {property_["type"]}')

    if not required:
        if "=" in type_hint:
            # in case the type hint has something it's equal to like a field
            chunks = type_hint.split(" =", maxsplit=1)
            type_hint = f"Optional[{chunks[0]}] = {chunks[1]}"
        else:
            type_hint = f"Optional[{type_hint}]"

    return type_hint, output_lines


def build_class_code(class_name: str, class_data: dict) -> List[str]:
    assert class_data["type"] == "object"
    assert class_data["additionalProperties"] == False

    output_lines = [
        f"class {class_name}(BaseModel):",
        f"\tclass Config:",
        f"\t\textra = Extra.forbid",
        f"",
    ]

    if "properties" in class_data:
        for property_name in class_data["properties"]:
            property_ = class_data["properties"][property_name]

            # compute the type hint
            type_hint, extra_lines = type_hint_for_property(
                property_,
                required=property_name in class_data["required"],
                name=property_name,
                parent_name=class_name,
            )

            # add extra lines first
            output_lines = extra_lines + output_lines

            # add the type hint
            output_lines.append(f"\t{property_name}: {type_hint}")

            # add a docstring if there is one
            if "description" in property_:
                output_lines.extend(['\t"""', "\t" + property_["description"], '\t"""'])

    # add a blank line at the end
    output_lines.append(f"")
    return output_lines


def main() -> None:
    output_file = THIS_DIR.joinpath("models2.py")

    # read in the api spec
    with open(THIS_DIR.joinpath("asyncapi.yml"), "r") as fp:
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
        "from __future__ import annotations",
        "from typing import List, Optional, Literal, Tuple",
        "from pydantic import BaseModel, Extra, Field",
        "",
        "",
    ]

    messages = asyncapi_data["components"]["messages"]
    for message in messages:
        print(f"Building code for {message}")
        final_output_lines.extend(
            build_class_code(message, messages[message]["payload"])
        )

    with open(output_file, "w") as fp:
        fp.write("\n".join(final_output_lines))


if __name__ == "__main__":
    main()
