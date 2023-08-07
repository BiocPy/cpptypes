import re

export_regex = re.compile("^\\s*//\\s*\\[\\[export\\]\\]")
comment_regex = re.compile("//")

class CppType:
    """C++ type, as parsed from the source file.

    Attributes:
        full_type (str): Full type name, including `const` qualifiers and pointers.
        base_type (str): Base type after removing all qualifiers and pointers.
        pointer_level (int): Number of pointer indirections.
        tags (set[str]): Additional user-supplied tags.
    """

    def __init__(self, full_type: str, base_type: str, pointer_level: int, tags: set[str]):
        """Construct a `CppType` instance from the supplied properties."""
        self.full_type = full_type
        self.base_type = base_type
        self.pointer_level = pointer_level
        self.tags = set(tags)

def create_type(fragments: list[str], tags: set[str]):
    base_type = []
    pointers = 0
    right_pointers = False

    for x in fragments:
        if not x or x == "const" or x == "&":
            continue
        elif x == "*":
            pointers += 1
        else:
            base_type.append(x)

    full_out = ""
    for x in fragments:
        if x == "*" or x == "&":
            full_out += x
        else:
            if full_out and full_out[-1] != "<" and full_out[-1] != "(":
                full_out += " "
            full_out += x

    return CppType(full_out, " ".join(base_type), pointers, tags)

class CppArgument:
    """Argument to a C++ function, as parsed from the source file.

    Attributes:
        name (str): Name of the argument.
        type (CppType): The type of the argument.
    """

    def __init__(self, name: str, type: CppType):
        """Construct a `CppArgument` instance from the supplied properties."""
        self.name = name
        self.type = type

class ExportTraverser:
    def __init__(self, handle):
        self.handle = handle
        self.line = ""
        self.position = 0

    def next(self):
        if self.position == len(self.line):
            self.line = self.handle.readline()
            self.position = 0
            if not self.line:
                raise ValueError("reached end of the file with an unterminated export")
        old = self.position
        self.position += 1
        return self.line[old]

    def back(self):  # this can only be called once after calling next().
        self.position -= 1

def add_to_type_fragment(fragment: str, chunks: list[str], nested: bool):
    if not nested:
        if fragment:
            chunks.append(fragment)
        return ""
    else:
        return fragment

def parse_component(grabber: ExportTraverser, as_argument: bool):
    current = ""
    chunks = []
    tags = []
    angle_nesting = 0
    curve_nesting = 0
    finished = False

    while True:
        x = grabber.next()

        if x.isspace():
            current = add_to_type_fragment(current, chunks, curve_nesting or angle_nesting)
            if current and current[-1] != "<" and current[-1] != "(" and current[-1] != " ":
                current += " "

        elif x == "/":
            x = grabber.next()

            # Comments terminate any existing chunk.
            if x == "/" or x == "*":
                current = add_to_type_fragment(current, chunks, curve_nesting or angle_nesting)
                if x == "/":
                    while True:
                        if grabber.next() == "\n":
                            break

                else:
                    x = grabber.next()

                    # We're inside a tag-enabled comment at the base nesting level, so we need to parse the tags.
                    if x == "*" and not curve_nesting and not angle_nesting:
                        curtag = ""
                        while True:
                            x = grabber.next()
                            if x.isspace():
                                if curtag:
                                    tags.append(curtag)
                                    curtag = ""
                            elif x == "*":
                                y = grabber.next()
                                if y == "/":
                                    if curtag:
                                        tags.append(curtag)
                                    break
                                else:
                                    curtag += x
                                    grabber.back()  # put it back for looping, as it might be a space.
                            else:
                                curtag += x

                    # Otherwise, just consuming the entire thing
                    else:
                        grabber.back()
                        while True:
                            if grabber.next() == "*":
                                if grabber.next() == "/":
                                    break

            else: 
                grabber.back()
                current += x

        elif x == "<":  # deal with templates.
            angle_nesting += 1
            current += x

        elif x == ">":
            if angle_nesting == 0:
                raise ValueError("imbalanced angle brackets at '" + grabber.line + "'")
            angle_nesting -= 1
            current += x
            current = add_to_type_fragment(current, chunks, curve_nesting or angle_nesting)

        elif x == "(":
            if as_argument:
                curve_nesting += 1
                current += x
            else:
                if curve_nesting == 0 and angle_nesting == 0:
                    if current == "" and len(chunks):  # e.g., if there's a space between the name and '('.
                        current = chunks.pop()
                    break
                curve_nesting += 1
                current += x

        elif x == ")":
            if as_argument and not curve_nesting and not angle_nesting:
                if current == "" and len(chunks):  # e.g., if there's a space between the final argument name and ')'.
                    current = chunks.pop()
                finished = True
                break

            if curve_nesting == 0:
                raise ValueError("imbalanced parentheses at '" + grabber.line + "'")
            current += x
            curve_nesting -= 1
            current = add_to_type_fragment(current, chunks, curve_nesting or angle_nesting)

        elif x == ",":
            if as_argument:
                if curve_nesting or angle_nesting:
                    current += x
                else:
                    if current == "" and len(chunks):
                        current = chunks.pop()
                    break
            else:
                current += x

        elif x == "*" or x == "&":
            current = add_to_type_fragment(current, chunks, angle_nesting or curve_nesting)
            if current:
                current += x
            else:
                chunks.append(x)

        else:
            current += x

    return current, create_type(chunks, tags), finished

def parse_cpp_file(path: str, all_functions: dict):
    with open(path, "r") as handle:
        while True:
            line = handle.readline()
            if not line:
                break

            if not export_regex.match(line):
                continue

            grabber = ExportTraverser(handle)

            funname, restype, finished = parse_component(grabber, False)

            all_args = []
            while not finished:
                name, argtype, finished = parse_component(grabber, True)
                if name: # avoid adding an empty argument.
                    all_args.append(CppArgument(name, argtype))

            all_functions[funname] = (restype, all_args)

def parse_cpp_exports(files: list[str]) -> dict[str, tuple[CppType, list[CppArgument]]]:
    """Parse C++ source files for tagged exports.

    Args:
        files (list[str]): Paths of C++ source files to parse. 

    Returns:
        Dict where keys are exported function names and values
        are a tuple of (return type, argument list).
    """
    all_functions = {}
    for p in files:
        try:
            parse_cpp_file(p, all_functions)
        except Exception as exc:
            raise ValueError("failed to parse '" + p + "'") from exc
    return all_functions
