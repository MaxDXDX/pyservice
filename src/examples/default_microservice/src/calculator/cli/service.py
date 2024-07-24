"""The CLI agent."""


import argparse

# pylint: disable=W0611
from calculator import manager, config
import sys

current_module = sys.modules[__name__]

parser = argparse.ArgumentParser(
    prog=f'CLI for {manager.app_ref}',
    description=f'Command line interface for {manager.app_ref}',
    epilog='Examples:')

parser.add_argument('service_object',
                    help='object of service')
parser.add_argument('object_attribute',
                    help='attribute of service')
parser.add_argument('argument', nargs='*',
                    help='arguments for object attribute')

if __name__ == '__main__':

    parsed, unknown = parser.parse_known_args()

    for arg in unknown:
        if arg.startswith(('-', '--')):
            # you can pass any arguments to add_argument
            parser.add_argument(arg.split('=')[0])

    args = parser.parse_args()
    service_object_name = args.service_object
    attribute_name = args.object_attribute
    positional_args = args.argument
    as_dict = vars(args)

    as_dict.pop('service_object')
    as_dict.pop('object_attribute')
    as_dict.pop('argument')

    keys_to_remove = []
    for k, v in as_dict.items():
        if v == []:
            keys_to_remove.append(k)

    for k in keys_to_remove:
        as_dict.pop(k)

    kwargs = as_dict

    service_object = getattr(sys.modules[__name__], service_object_name)
    attribute = getattr(service_object, attribute_name)
    if callable(attribute):
        print(attribute(*positional_args, **kwargs))
    else:
        print(attribute)
