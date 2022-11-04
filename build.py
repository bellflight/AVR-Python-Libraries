import argparse
import os
from typing import List

import commentjson
import jinja2

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
MQTT_DIR = os.path.join(THIS_DIR, "bell", "avr", "mqtt")


def titleify(text: str) -> str:
    return "".join(i.title() for i in text.replace("_", "/").split("/"))


def process_klass(klass: dict) -> List[dict]:
    """
    Take an class and generate a list a new classes that also need to be generated.
    Acts recursively.
    """
    # list to hold the new generated classes
    new_klasses = []

    for item in klass["payload"]:
        if not isinstance(item["type"], str):
            # if the type of a key is not a string, create a new helper class for it
            # and replace it with a reference to that class
            new_class_name = klass["name"] + titleify(item["key"])
            # copy over the documentation as well if present
            new_klasses.append(
                {
                    "name": new_class_name,
                    "payload": item["type"],
                    "docs": item.get("docs", ""),
                }
            )
            item["type"] = new_class_name

    # list to hold the newly proccessed new classes
    new_new_klasses = []
    for new_klass in new_klasses:
        new_new_klasses.extend(process_klass(new_klass))

    # return the new klasses and their children
    return new_klasses + new_new_klasses


def main(docs: bool) -> None:
    # setup jinja
    template_loader = jinja2.FileSystemLoader(searchpath=MQTT_DIR)
    template_env = jinja2.Environment(loader=template_loader)

    # load data
    print("Loading message definitions")
    with open(os.path.join(MQTT_DIR, "messages.jsonc"), "r") as fp:
        messages = commentjson.load(fp)["messages"]

    # generate addtional class configuration
    # we need to do some pre-processing to make templating easier
    print("Preprocessing message definitions")
    klasses = []
    for message in messages:
        if "name" not in message:
            # generate a class name
            message["name"] = titleify(message["topic"])

        # prepend path to topics docs
        if "docs" not in message:
            message["docs"] = []

        orig_docs = message["docs"]
        message["docs"] = [f"Topic: `{message['topic']}`"]

        if orig_docs:
            message["docs"].extend([""])
            message["docs"].extend(orig_docs)

        # add generated klasses to seperate list
        klasses.extend(process_klass(message))

    # sort klasses and messages
    messages = sorted(messages, key=lambda x: x["name"])
    klasses = sorted(klasses, key=lambda x: x["name"])

    # generate python code
    constants_template = template_env.get_template("constants.j2")

    print("Rendering constants template")
    with open(os.path.join(MQTT_DIR, "constants.py"), "w") as fp:
        fp.write(constants_template.render(klasses=klasses, messages=messages))

    payloads_template = template_env.get_template("payloads.j2")

    print("Rendering payloads template")
    with open(os.path.join(MQTT_DIR, "payloads.py"), "w") as fp:
        fp.write(payloads_template.render(klasses=klasses, messages=messages))

    client_template = template_env.get_template("client.j2")

    print("Rendering client template")
    with open(os.path.join(MQTT_DIR, "client.py"), "w") as fp:
        fp.write(client_template.render(klasses=klasses, messages=messages))

    # generate documentation
    if docs:
        template = template_env.get_template("docs.j2")

        print("Rendering documentation template")
        with open(os.path.join(THIS_DIR, "README.md"), "a") as fp:
            fp.write(template.render(klasses=klasses, messages=messages))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs", action="store_true", help="Generate documentation")
    args = parser.parse_args()

    main(args.docs)
