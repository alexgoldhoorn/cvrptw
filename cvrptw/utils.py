import json
import numpy as np
import numbers
from typing import Dict, List


def prepare_data_for_json(d):
    """Return value that has simple types and are serializable with json.dump."""
    result = d
    if type(d) is dict:
        result = dict()
        for k, v in d.items():
            result[k] = prepare_data_for_json(v)
    elif type(d) is list:
        result = []
        for x in d:
            result.append(prepare_data_for_json(x))
    elif type(d) is np.int64 or type(d) is np.int32:
        result = int(d)
    elif type(d) is np.cfloat:
        result = float(d)
    elif type(d) is np.ndarray:
        result = d.tolist()

    return result


def save_as_json(result: dict, out_file: str):
    clean_dict = prepare_data_for_json(result)
    with open(out_file, "w") as f:
        json.dump(clean_dict, f, indent=4)


def show_dict(d: dict, indent=0, header=None):
    """Show a dictionary pretty printed.
    Note: can't use json.dumps because it does not support all used variable types.
    """
    if header:
        print()
        print(f"---{header}---")

    indent_str = " " * indent
    for k, v in d.items():
        if type(v) is dict:
            print(f"{indent_str}** {k} **")
            show_dict(v, indent + 4)
        elif type(v) is list and len(v) > 0 and type(v[0]) is dict:
            for i, x in enumerate(v):
                print(f"{indent_str}{i})")
                show_dict(x, indent + 4)
        elif isinstance(v, numbers.Number) or type(v) is str:
            print(f"{indent_str}{k} = {v}")
        else:
            print(f"{indent_str}** {k} **")
            print(f"{indent_str}{v}")

    if header:
        print("--- ---")
        print()


def convert_field_to_int(data: Dict[str, List], field: str):
    """
    Assure that all fields are int, if they are float they are rounded.

    Args:
        data:   dict of arrays (normal or Numpy array)
        field:  field in the dict to convert
    """
    if type(data[field]) is list:
        if len(data[field]) > 0:
            if type(data[field][0]) is int:
                return  # int already
            elif type(data[field][0]) is float:
                data[field] = list(map(lambda x: int(round(x)), data[field]))
            else:
                raise Exception(
                    f"Unknown data type ({type(data[field][0])}) for {field}"
                )
    else:
        # numpy array
        if data[field].dtype.kind == "i":
            return  # is int already
        elif data[field].dtype.kind != "f":
            raise Exception(f"Unknown data type ({data[field].dtype}) for {field}")

        data[field] = data[field].round().astype(np.int64)
