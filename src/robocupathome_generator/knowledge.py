import re
import warnings
from dataclasses import dataclass
from functools import cached_property

@dataclass(frozen=True)
class Category:
    singular: str
    plural: str

@dataclass
class Knowledge:
    names: list[str]
    locations: list[str]
    placement_locations: list[str]
    rooms: list[str]
    objects_by_category: dict[str, list[str]]
    categories: list[Category]
    storages: dict[str, str]

    @cached_property
    def objects(self) -> list[str]:
        return [
            obj
            for objs in self.objects_by_category.values()
            for obj in objs
        ]

    @cached_property
    def object_categories_plural(self) -> list[str]:
        return [c.plural for c in self.categories]

    @cached_property
    def object_categories_singular(self) -> list[str]:
        return [c.singular for c in self.categories]


def _read_data(file_path: str) -> str:
    with open(file_path, "r") as file:
        return file.read()


def _parse_names(data: str) -> list[str]:
    parsed_names = re.findall(r"\|\s*([A-Za-z]+)\s*\|", data, re.DOTALL)
    parsed_names = [name.strip() for name in parsed_names]

    if parsed_names:
        return parsed_names[1:]
    warnings.warn("List of names is empty. Check content of names markdown file")
    return []


def _parse_locations(data: str):
    matches = re.findall(
        r"\|\s*([0-9]+)\s*\|\s*([A-Za-z\s\(\)]+?)\s*\|\s*([A-Za-z\s]*)\|",
        data,
        re.DOTALL,
    )

    parsed_locations = []
    parsed_placement_locations = []
    category_dict: dict[str, list[str]] = {}

    for _, name, category in matches:
        name = name.strip()
        category = category.strip()

        is_placement = name.endswith("(p)")
        clean_name = name.replace("(p)", "").strip()

        parsed_locations.append(clean_name)

        if is_placement:
            parsed_placement_locations.append(clean_name)

        if category:
            category_dict.setdefault(category, []).append(clean_name)

    if parsed_locations:
        return parsed_locations, parsed_placement_locations, category_dict

    warnings.warn("List of locations is empty. Check content of location markdown file")
    return [], [], {}


def _parse_rooms(data: str) -> list[str]:
    parsed_rooms = re.findall(r"\|\s*(\w+ \w*)\s*\|", data, re.DOTALL)
    parsed_rooms = [room.strip() for room in parsed_rooms]

    if parsed_rooms:
        return parsed_rooms[1:]
    warnings.warn("List of rooms is empty. Check content of room markdown file")
    return []


def _parse_objects(data: str):
    class_blocks = re.split(r"# Class\s+", data)
    class_blocks = [b.strip() for b in class_blocks if b.strip()]

    objects_by_category: dict[str, list[str]] = {}
    categories: list[Category] = []

    for block in class_blocks:
        header_match = re.match(r"([\w_]+)\s*\(([\w_]+)\)", block)
        if not header_match:
            continue

        plural = header_match.group(1).replace("_", " ").strip()
        singular = header_match.group(2).replace("_", " ").strip()

        categories.append(Category(singular=singular, plural=plural))

        objects = re.findall(r"\|\s*([\w_]+)\s*\|", block)
        objects = [
            obj.replace("_", " ").strip()
            for obj in objects
            if obj != "Objectname"
        ]

        objects_by_category[plural] = objects

    if objects_by_category:
        return objects_by_category, categories

    warnings.warn("Object markdown file is empty or malformed")
    return {}, []


def parse_data(data_dir: str) -> Knowledge:
    names = _parse_names(_read_data(f"{data_dir}/names/names.md"))

    locations, placement_locations, location_categories = _parse_locations(
        _read_data(f"{data_dir}/maps/location_names.md")
    )

    rooms = _parse_rooms(_read_data(f"{data_dir}/maps/room_names.md"))

    objects_by_category, object_categories = _parse_objects(
        _read_data(f"{data_dir}/objects/objects.md")
    )

    return Knowledge(
        names=names,
        locations=locations,
        placement_locations=placement_locations,
        rooms=rooms,
        objects_by_category=objects_by_category,
        categories=object_categories,
        storages=location_categories,
    )

if __name__ == '__main__':
    import argparse 
    parser = argparse.ArgumentParser() 
    from robocupathome_generator.generator import dir_path 
    parser.add_argument( "-d", "--data-dir", default=".", help="directory where the data is read from", type=dir_path, ) 
    args = parser.parse_args() 
    db = parse_data(args.data_dir) 
    import pprint 
    pprint.pprint(db, width=120)