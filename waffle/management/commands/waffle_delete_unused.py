import os
import pathlib

from django.core.management.base import BaseCommand
from waffle import (
    get_waffle_flag_model,
    get_waffle_switch_model,
    get_waffle_sample_model,
)


class Command(BaseCommand):
    help = "Delete flags, samples, and switches not present in the code from the Database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Do not delete anything, just show what would be deleted",
        )
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="Do not prompt for confirmation",
        )
        parser.add_argument(
            "--switches",
            action="store_true",
            help="Remove unused switches",
        )
        parser.add_argument(
            "--flags",
            action="store_true",
            help="Remove unused flags",
        )
        parser.add_argument(
            "--samples",
            action="store_true",
            help="Remove unused samples",
        )

    def handle(self, *args, **kwargs):
        no_input = kwargs["no_input"]
        delete_switches = kwargs["switches"]
        delete_flags = kwargs["flags"]
        delete_samples = kwargs["samples"]
        if delete_switches:
            self.delete_model(get_waffle_switch_model(), no_input)
        if delete_flags:
            self.delete_model(get_waffle_flag_model(), no_input)
        if delete_samples:
            self.delete_model(get_waffle_sample_model(), no_input)

    def delete_model(self, model, no_input):
        items = model.objects.all()
        for item in items:
            if not expression_exists(item.name):
                self.stdout.write("%s %s not found in the code" % (model.__name__, item.name))
                if no_input or self.confirm("Delete %s ?" % model.__name__):
                    self.stdout.write("Deleting switch")
                    item.delete()
            else:
                self.stdout.write("%s %s found in the code" % (model.__name__, item.name))

    def confirm(self, question):
        answer = input(question + " [y/N] ").strip()
        return answer.lower() == "y"


def expression_in_file(expression, filename):
    with open(filename) as file:
        content = file.read()
        return expression in content


def expression_exists(expression):
    for root, dirs, files in os.walk(os.getcwd()):
        for file in files:
            if not (file.endswith(".py") or file.endswith(".html")): #TODO: make this a list of extensions
                continue
            filename = pathlib.Path(root) / file
            if expression_in_file(expression, filename):
                return True
    return False
