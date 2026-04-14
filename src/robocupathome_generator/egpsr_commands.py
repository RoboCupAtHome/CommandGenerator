import random
import re
import itertools
import warnings
from robocupathome_generator.gpsr_commands import CommandGenerator
from dataclasses import dataclass
from enum import Enum
import random


class TaskCategory(Enum):
    TRASH = 1
    OBJECT = 2
    PERSON = 3


@dataclass
class CommandSetup:
    category: TaskCategory
    task: str


class EgpsrCommandGenerator:

    def __init__(self, gpsr_generator):
        self.gpsr_generator = gpsr_generator

    def generate_setup(self, number: int):
        if number < 2:
            raise Exception("too low")

        problems = []
        problems.append(self._generate_person_task("objects"))
        problems.append(self._generate_person_task("objects"))
        problems.append(self._generate_person_task("objects"))

        # 25% - 50% are trash tasks
        trash_tasks = random.randint(number // 4, number // 2)
        object_tasks = number - trash_tasks

        for _ in range(trash_tasks):
            problems.append(self._generate_trash_task())

        for _ in range(object_tasks):
            problems.append(self._generate_object_task())

        return problems

    def generate_task(self, category: TaskCategory):
        match category:
            case TaskCategory.TRASH:
                return self._generate_trash_task()
            case TaskCategory.PERSON:
                categories = ["people", "objects"]
                return self._generate_person_task(random.choice(categories))
            case TaskCategory.OBJECT:
                return self._generate_object_task()

    def _generate_person_task(self, cat):
        command = self.gpsr_generator.generate_command_start(cmd_category=cat)
        task = self.gpsr_generator.insert_all_placeholders(
            "There is a person at the {loc}, their request is:"
        )
        task += f"\n\t {command}"
        return CommandSetup(TaskCategory.PERSON, task)

    def _generate_trash_task(self):
        task = self.gpsr_generator.insert_all_placeholders(
            "Put an object on the floor {inRoom}"
        )
        return CommandSetup(TaskCategory.TRASH, task)

    def _generate_object_task(self):
        task = self.gpsr_generator.insert_all_placeholders(
            "The {obj} is at the {plcmtLoc}"
        )
        return CommandSetup(TaskCategory.OBJECT, task)

    def regenerate(self, problems, id):
        task: CommandSetup = problems[id]
        problems[id] = self.generate_task(task.category)
        return problems
