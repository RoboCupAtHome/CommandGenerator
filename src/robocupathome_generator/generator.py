import random
import re
import warnings
import os

import argparse
import qrcode

from PIL import Image, ImageDraw, ImageFont
from robocupathome_generator.gpsr_commands import CommandGenerator
from robocupathome_generator.egpsr_commands import EgpsrCommandGenerator
from robocupathome_generator.knowledge import Knowledge, parse_data

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
    knowledge
):
    generator = CommandGenerator(knowledge)
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


def print_config(knowledge: Knowledge):
    print(f"Names: \n{knowledge.names}")
    print(f"Locations: \n{knowledge.locations}")
    print(f"Locations (p): \n{knowledge.placement_locations}")
    print(f"Rooms: \n{knowledge.rooms}")
    print(f"Objects: \n{knowledge.objects}")
    print(f"Categories: \n{knowledge.categories}")


def createGPSRGenerator(data_dir) -> CommandGenerator:
    knowledge = parse_data(data_dir)
    return CommandGenerator(knowledge)

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
    parser.add_argument(
        "-g", "--generate", action="store_true", help="generate 5000 commands to check for errors"
    )

    args = parser.parse_args()
    knowledge = parse_data(args.data_dir)

    if args.print_config:
        print_config(knowledge)
    elif args.generate:
        generator = CommandGenerator(knowledge)
        for _ in range(5000):
            command = generator.generate_command_start(cmd_category="")
            command = command[0].upper() + command[1:]
            print(command)
    else:
        generator(knowledge)
