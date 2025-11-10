import random
import re
import warnings
import os

import argparse
import qrcode

from PIL import Image, ImageDraw, ImageFont
from robocupathome_generator.gpsr_commands import CommandGenerator
from robocupathome_generator.egpsr_commands import EgpsrCommandGenerator


def read_data(file_path):
    with open(file_path, "r") as file:
        data = file.read()
    return data


def parse_names(data):
    parsed_names = re.findall(r"\|\s*([A-Za-z]+)\s*\|", data, re.DOTALL)
    parsed_names = [name.strip() for name in parsed_names]

    if parsed_names:
        return parsed_names[1:]
    else:
        warnings.warn("List of names is empty. Check content of names markdown file")
        return []


def parse_locations(data):
    parsed_locations = re.findall(
        r"\|\s*([0-9]+)\s*\|\s*([A-Za-z,\s, \(,\)]+)\|", data, re.DOTALL
    )
    parsed_locations = [b for (a, b) in parsed_locations]
    parsed_locations = [location.strip() for location in parsed_locations]

    parsed_placement_locations = [
        location for location in parsed_locations if location.endswith("(p)")
    ]
    parsed_locations = [location.replace("(p)", "") for location in parsed_locations]
    parsed_placement_locations = [
        location.replace("(p)", "") for location in parsed_placement_locations
    ]
    parsed_placement_locations = [
        location.strip() for location in parsed_placement_locations
    ]
    parsed_locations = [location.strip() for location in parsed_locations]

    if parsed_locations:
        return parsed_locations, parsed_placement_locations
    else:
        warnings.warn(
            "List of locations is empty. Check content of location markdown file"
        )
        return []


def parse_rooms(data):
    parsed_rooms = re.findall(r"\|\s*(\w+ \w*)\s*\|", data, re.DOTALL)
    parsed_rooms = [rooms.strip() for rooms in parsed_rooms]

    if parsed_rooms:
        return parsed_rooms[1:]
    else:
        warnings.warn("List of rooms is empty. Check content of room markdown file")
        return []


def parse_objects(data):
    parsed_objects = re.findall(r"\|\s*(\w+)\s*\|", data, re.DOTALL)
    parsed_objects = [objects for objects in parsed_objects if objects != "Objectname"]
    parsed_objects = [objects.replace("_", " ") for objects in parsed_objects]
    parsed_objects = [objects.strip() for objects in parsed_objects]

    parsed_categories = re.findall(r"# Class \s*([\w,\s, \(,\)]+)\s*", data, re.DOTALL)
    parsed_categories = [category.strip() for category in parsed_categories]
    parsed_categories = [
        category.replace("(", "").replace(")", "").split()
        for category in parsed_categories
    ]
    parsed_categories_plural = [category[0] for category in parsed_categories]
    parsed_categories_plural = [
        category.replace("_", " ") for category in parsed_categories_plural
    ]
    parsed_categories_singular = [category[1] for category in parsed_categories]
    parsed_categories_singular = [
        category.replace("_", " ") for category in parsed_categories_singular
    ]

    if parsed_objects or parsed_categories:
        return parsed_objects, parsed_categories_plural, parsed_categories_singular
    else:
        warnings.warn(
            "List of objects or object categories is empty. Check content of object markdown file"
        )
        return []


def dir_path(path):
    if os.path.isdir(path):
        return path
    else:
        raise argparse.ArgumentTypeError(f"'{path}' is not a valid path")


user_prompt = """
'1': Any command
'2': Command without manipulation
'3': Command with manipulation
'4': Batch of three commands
'5': Generate EGPSR setup
'0': Generate QR code
'q': Quit"
"""

reroll_prompt = "insert number to reroll, 'r' to regenerate all"


def generator(
    names,
    location_names,
    placement_location_names,
    room_names,
    object_names,
    object_categories_plural,
    object_categories_singular,
):
    generator = CommandGenerator(
        names,
        location_names,
        placement_location_names,
        room_names,
        object_names,
        object_categories_plural,
        object_categories_singular,
    )
    egpsr_generator = EgpsrCommandGenerator(generator)

    print(user_prompt)
    command = ""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=30,
        border=4,
    )
    last_input = "?"
    try:
        while True:
            # Read user input
            user_input = input()

            # Check user input
            if user_input == "1":
                command = generator.generate_command_start(cmd_category="")
                last_input = "1"
            elif user_input == "2":
                command = generator.generate_command_start(cmd_category="people")
                last_input = "2"
            elif user_input == "3":
                command = generator.generate_command_start(cmd_category="objects")
                last_input = "3"
            elif user_input == "4":
                command_one = generator.generate_command_start(cmd_category="people")
                command_two = generator.generate_command_start(cmd_category="objects")
                command_three = generator.generate_command_start(cmd_category="")
                command_list = [
                    command_one[0].upper() + command_one[1:],
                    command_two[0].upper() + command_two[1:],
                    command_three[0].upper() + command_three[1:],
                ]
                random.shuffle(command_list)
                command = (
                    command_list[0] + "\n" + command_list[1] + "\n" + command_list[2]
                )
                last_input = "4"
            elif user_input == "5":
                print("how many non person tasks should be created?")
                num = int(input())
                print("\n")
                commands = egpsr_generator.generate_setup(num)
                last_input = "5"
                while user_input != "q":
                    command = ""
                    for i, task in enumerate(commands):
                        command += f"{i}.) {task.task}\n"
                    print(command)
                    print(reroll_prompt)
                    user_input = input()
                    if user_input.isdigit():
                        n = int(user_input)
                        if n < len(commands):
                            commands = egpsr_generator.regenerate(commands, n)
                    elif user_input == "r":
                        commands = egpsr_generator.generate_setup(num)
                    else:
                        break

            elif user_input == "q":
                break
            elif user_input == "0":
                if last_input == "4":
                    commands = command_list
                else:
                    commands = [command]
                for c in commands:
                    qr.clear()
                    qr.add_data(c)
                    qr.make(fit=True)

                    img = qr.make_image(fill_color="black", back_color="white")
                    # Create a drawing object
                    draw = ImageDraw.Draw(img)

                    fontsize = 30
                    # Load a font
                    while True:
                        font = ImageFont.load_default(fontsize)
                        max = int((img.size[0] / (draw.textlength("W", font) + 1)))

                        if len(c) > max:
                            split = [c[i : i + max] for i in range(0, len(c), max)]

                            if len(split) < 4:
                                c = "\n".join(split)
                                break
                            else:
                                fontsize -= 4
                        else:
                            break

                    # Draw text on the image
                    draw.multiline_text(
                        (img.size[0] / 2, img.size[1]),
                        c,
                        font=font,
                        fill="black",
                        anchor="md",
                    )
                    img.show()
            else:
                print(user_prompt)
                continue
            command = command[0].upper() + command[1:]
            print(command)

    except KeyboardInterrupt:
        print("KeyboardInterrupt. Exiting the loop.")


def print_config(
    names,
    location_names,
    placement_location_names,
    room_names,
    object_names,
    object_categories_plural,
    object_categories_singular,
):
    print(f"Names: \n{names}")
    print(f"Locations: \n{location_names}")
    print(f"Locations (p): \n{placement_location_names}")
    print(f"Rooms: \n{room_names}")
    print(f"Objects: \n{object_names}")
    print(
        f"Categories: \n{list(zip(object_categories_singular,object_categories_plural))}"
    )


def createGPSRGenerator(data_dir) -> CommandGenerator:
    names_file_path = f"{data_dir}/names/names.md"
    locations_file_path = f"{data_dir}/maps/location_names.md"
    rooms_file_path = f"{data_dir}/maps/room_names.md"
    objects_file_path = f"{data_dir}/objects/objects.md"

    names_data = read_data(names_file_path)
    names = parse_names(names_data)

    locations_data = read_data(locations_file_path)
    location_names, placement_location_names = parse_locations(locations_data)

    rooms_data = read_data(rooms_file_path)
    room_names = parse_rooms(rooms_data)

    objects_data = read_data(objects_file_path)
    object_names, object_categories_plural, object_categories_singular = parse_objects(
        objects_data
    )
    return CommandGenerator(
        names,
        location_names,
        placement_location_names,
        room_names,
        object_names,
        object_categories_plural,
        object_categories_singular,
    )



def main():
    parser = argparse.ArgumentParser(
        prog="athome-generator",
        description="Generate Commands for Robocup@Home",
        epilog="",
    )
    parser.add_argument(
        "-d",
        "--data-dir",
        default=".",
        help="directory where the data is read from",
        type=dir_path,
    )
    parser.add_argument(
        "-p", "--print-config", action="store_true", help="print parsed data and exit"
    )

    args = parser.parse_args()

    names_file_path = f"{args.data_dir}/names/names.md"
    locations_file_path = f"{args.data_dir}/maps/location_names.md"
    rooms_file_path = f"{args.data_dir}/maps/room_names.md"
    objects_file_path = f"{args.data_dir}/objects/objects.md"

    names_data = read_data(names_file_path)
    names = parse_names(names_data)

    locations_data = read_data(locations_file_path)
    location_names, placement_location_names = parse_locations(locations_data)

    rooms_data = read_data(rooms_file_path)
    room_names = parse_rooms(rooms_data)

    objects_data = read_data(objects_file_path)
    object_names, object_categories_plural, object_categories_singular = parse_objects(
        objects_data
    )

    if args.print_config:
        print_config(
            names,
            location_names,
            placement_location_names,
            room_names,
            object_names,
            object_categories_plural,
            object_categories_singular,
        )
    else:
        generator(
            names,
            location_names,
            placement_location_names,
            room_names,
            object_names,
            object_categories_plural,
            object_categories_singular,
        )

    # for _ in range(500):  # Generate 50 random commands
    #     generator = CommandGenerator(names, location_names, placement_location_names, room_names, object_names,
    #                                  object_categories_plural, object_categories_singular)
    #     command = generator.generate_command_start(cmd_category="")
    #     command = command[0].upper() + command[1:]
    #     print(command)
