#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re
import os
from jinja2 import Environment, FileSystemLoader
import textfsm
from json2xml import json2xml
import jinja_filters
import csv
import argparse


def process_fsms(config_text):
    """
    Process the FSM templates in the 'parser' directory and parse the given configuration text.

    Args:
        config_text (str): The configuration text to be parsed.

    Returns:
        dict: A dictionary with keys as FSM template names and values as parsed results.
    """
    result = {}

    fsms = [
        f for f in os.listdir("app/parser") if os.path.isfile(os.path.join("app/parser", f))
    ]
    for fsm in fsms:
        if fsm.endswith(".textfsm"):
            key = fsm.replace(".textfsm", "")
            result[key] = process_fsm(f"app/parser/{fsm}", config_text)

    return result


def process_fsm(path, raw):
    """
    Process a single FSM template and parse the given raw text.

    Args:
        path (str): The path to the FSM template.
        raw (str): The raw text to be parsed.

    Returns:
        list: A list of dictionaries containing parsed results.
    """
    with open(path) as template:
        fsm = textfsm.TextFSM(template)
        result = fsm.ParseTextToDicts(raw)
    return result


def prune_empty_tables(tables):
    """
    Remove empty tables from the parsed results.

    Args:
        tables (dict): A dictionary containing parsed tables.

    Returns:
        dict: A dictionary with empty tables removed.
    """
    keys_to_be_removed = []
    for key, value in tables.items():
        if len(tables[key]) == 0:
            keys_to_be_removed.append(key)
    for k in keys_to_be_removed:
        del tables[k]

    return tables


def post_process_fsms(tables):
    """
    Post-process the parsed FSM tables using Jinja2 templates.

    Args:
        tables (dict): A dictionary containing parsed tables.

    Returns:
        dict: A dictionary with post-processed tables.
    """
    file_loader = FileSystemLoader("app/parser")
    env = Environment(loader=file_loader)
    env.filters["hyphen_range_to_list"] = jinja_filters.hyphen_range_to_list
    env.filters["merge_table_by_key"] = jinja_filters.merge_table_by_key
    env.filters["table_flatten"] = jinja_filters.table_flatten

    result = {}
    for key, value in tables.items():
        if os.path.isfile(f"app/parser/{key}.json.j2"):
            template = env.get_template(f"{key}.json.j2")
            data = {"data": value}
            parse = template.render(data)
            result[key] = json.loads(parse)
        else:
            result[key] = value

    return result


def convert(tables, converter, options=None):
    """
    Convert the parsed tables using Jinja2 templates in the specified converter directory.

    Args:
        tables (dict): A dictionary containing parsed tables.
        converter (str): The name of the converter directory.
        options (dict, optional): Additional options for conversion.

    Returns:
        dict: A dictionary with converted results.
    """
    result = {}
    converter_path = f"app/converter/{converter}"
    tables["options"] = options
    parents = next(os.walk(converter_path))[1]
    for parent in parents:
        result[parent] = []
        # parse each jinja
        parent_path = f"{converter_path}/{parent}"
        jinjas = [
            f
            for f in os.listdir(parent_path)
            if os.path.isfile(os.path.join(parent_path, f))
        ]
        for jinja in jinjas:
            if jinja.endswith(".j2"):
                # do jinja processing
                file_loader = FileSystemLoader(f"{parent_path}")
                env = Environment(
                    loader=file_loader, trim_blocks=True, lstrip_blocks=True
                )
                template = env.get_template(jinja)
                rendered = template.render(tables)
                try:
                    result[parent] = result[parent] + json.loads(rendered)
                except json.decoder.JSONDecodeError:
                    print(f"Error parsing using {jinja}")
                    print(f"{rendered}")
                    raise
    return result


def parse_input(config_text):
    """
    Parse the input configuration text and process FSMs.

    Args:
        config_text (str): The configuration text to be parsed.

    Returns:
        dict: A dictionary with processed FSM tables.
    """
    tables = process_fsms(config_text)
    tables = prune_empty_tables(tables)
    processed = post_process_fsms(tables)
    return processed


def json_2_xml(data):
    """
    Convert JSON data to XML format.

    Args:
        data (dict): The JSON data to be converted.

    Returns:
        str: The XML representation of the JSON data.
    """
    xml = json2xml.Json2xml(
        data, wrapper="config", attr_type=False, item_wrap=False
    ).to_xml()
    replaced = re.sub(r"<xml_container>", "", xml)
    replaced = re.sub(r"</xml_container>", "", replaced)
    return replaced


def handler(event, context):
    """
    AWS Lambda handler function to process the event and return the converted XML and tables.

    Args:
        event (dict): The event data.
        context (object): The context object.

    Returns:
        dict: The response containing the status code, headers, and body with the converted results.
    """
    print("received event:")
    print(json.dumps(event))
    body = json.loads(event["body"])
    print("received body:")
    print(json.dumps(body))

    if not body:
        return {"statusCode": 400, "body": json.dumps("Missing body")}
    config = body["config"]
    options = body["options"]
    print(options)
    tables = parse_input(config)

    converted = convert(tables, "default", options)
    xml = json_2_xml(converted)
    print(f"returning xml: {xml}")

    result = {"message": "success", "xml": xml, "tables": tables}
    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
        },
        "body": json.dumps(result),
    }


def json_2_saos(input):
    """
    Convert JSON data to SAOS configuration commands.

    Args:
        input (dict): The JSON data to be converted.

    Returns:
        str: The SAOS configuration commands.
    """
    out = []

    # I need to process every command in a nested way also take on consideration the lists
    def reduce(nested_json, cmd="", name=""):
        # cmd is the previous build
        if type(nested_json) is dict:
            # The name is the key element and must be in every command in the first place
            if "name" in nested_json.keys():
                name = nested_json["name"] + " "
                del nested_json["name"]
            for a in nested_json:
                reduce(nested_json[a], cmd + name + a + " ")
        elif type(nested_json) is list:
            for a in nested_json:
                reduce(a, cmd)
        else:
            out.append(cmd[:-1] + " " + nested_json)

    reduce(input, "config ")

    strout = "\n".join(out)

    return strout


if __name__ == "__main__":
    # Run local conversion and tests

    parser = argparse.ArgumentParser(description="Process SAOS configurations.")
    parser.add_argument("--examples", action="store_true", help="Process examples directory")
    args = parser.parse_args()

    def get_files_by_extension_in_directory(directory, include_examples=False):
        """
        Get a list of all files in the given directory, optionally including the examples directory.

        Args:
            directory (str): The directory to search for files.
            include_examples (bool): Whether to include files in the examples directory.

        Returns:
            list: A list of file names.
        """
        files = [
            f
            for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f))
        ]
        if include_examples:
            examples_dir = os.path.join(directory, "examples")
            if os.path.exists(examples_dir):
                files += [
                    os.path.join("examples", f)
                    for f in os.listdir(examples_dir)
                    if os.path.isfile(os.path.join(examples_dir, f))
                ]
        return files

    def write_file(data, destination):
        """
        Write data to a file at the specified destination.

        Args:
            data (str): The data to be written.
            destination (str): The file path where the data will be written.
        """
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        with open(destination, "w") as file:
            file.write(data)

    def generate_csv(filename, tables):
        """
        Generate CSV files from the parsed tables.

        Args:
            filename (str): The name of the input file.
            tables (dict): A dictionary containing parsed tables.

        Returns:
            int: The total number of commands parsed.
        """
        counter = 0
        for key, value in tables.items():

            header = []
            for k, v in value[0].items():
                header.append(k)
            filename_short = filename.replace(".saos", "").replace("configs/", "")
            os.makedirs(f"app/assets/{filename_short}", exist_ok=True)
            with open(
                f"app/assets/{filename_short}/{key}.csv", "w", newline=""
            ) as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=header)
                writer.writeheader()
                for x in value:
                    counter += 1
                    writer.writerow(x)
        return counter

    files = get_files_by_extension_in_directory("saos6-configs", include_examples=args.examples)
    f = open(
        f"app/converter/default/options.json",
    )
    options = json.load(f)
    cmds_total = 0
    cmds_converted = 0
    for file in files:
        print("#" * 30)
        print(f"Parsing input {file}")
        config_text = open(f"saos6-configs/{file}").read()
        cmds_total = len(
            [ele for ele in config_text.replace(" ", "").split("\n") if ele != ""]
        )  # Num of commands = num of not empty lines
        tables = parse_input(config_text)
        cmds_parsed = generate_csv(
            file, tables
        )  # Each line generated in the CSV is going to be a command that was parsed TODO
        # print(f"converting input for {file}")
        converted = convert(tables, "default", options)
        xml = json_2_xml(converted)
        saos = json_2_saos(converted)
        # print(f"writing output for {file}")
        filename = file.replace(".saos", "")
        os.makedirs(f"app/assets/{filename}", exist_ok=True)
        write_file(
            json.dumps(converted, indent=2, sort_keys=True),
            f"app/assets/{filename}/{filename}.json",
        )
        os.makedirs(f"output/xml/", exist_ok=True)
        os.makedirs(f"output/saos10/", exist_ok=True)
        write_file(xml, f"output/xml/{filename}.xml")
        write_file(saos, f"output/saos10/{filename}.saos")
        # print(f"done for {file}")
        print(f"{round((cmds_parsed/cmds_total)*100,2)}% parse rate")
        print(f"{cmds_parsed} commands were recognized out of {cmds_total}")
