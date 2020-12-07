import re
import textwrap
from collections import namedtuple
from typing import List, Optional

Parameter = namedtuple("Parameter", ["name", "type", "desc"])


def docstring_to_param_list(docstring: Optional[str]) -> List[Parameter]:
    """Extract Parameters section from numpy docstring."""
    if not docstring:
        return []
    splits = re.split(r"Parameters[\s-]+\n", docstring)
    if len(splits) < 2:
        return []
    content = splits[1].split("\n\n")[0].rstrip()
    lines = textwrap.dedent(content).splitlines()
    params = []
    while lines:
        header = lines.pop(0)
        if " :" in header:
            arg_name, arg_type = header.split(" :", maxsplit=1)
            arg_name, arg_type = arg_name.strip(), arg_type.strip()
        else:
            arg_name, arg_type = header, ""

        desc = []
        while lines and lines[0].startswith((" ", "\t")):
            desc.append(lines.pop(0))
        desc = textwrap.dedent("\n".join(desc)).split("\n")
        params.append(Parameter(arg_name, arg_type, desc))
    return params


def param_list_to_str(param_list: List[Parameter]) -> List[str]:
    """Format Parameters section for numpy docstring from list of tuples."""
    out = []
    out += ["Parameters", len("Parameters") * "-"]
    for param in param_list:
        parts = []
        if param.name:
            parts.append(param.name)
        if param.type:
            parts.append(param.type)
        out += [" : ".join(parts)]
        if param.desc and "".join(param.desc).strip():
            out += [" " * 4 + line for line in param.desc]
    out += [""]
    return out
