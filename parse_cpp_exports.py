import os
import re

export_regex = re.compile("^\\s*//\\s*\\[\\[export\\]\\]")
comment_regex = re.compile("//")

class CppType:
    def __init__(self, full_type, base_type, pointer_level, tags):
        self.full_type = full_type
        self.base_type = base_type
        self.pointer_level = pointer_level
        self.tags = set(tags)

    @classmethod
    def create(cls, fragments, tags):
        base_type = []
        pointers = 0
        right_pointers = False 

        for x in fragments:
            while x and x.startswith("*"):
                pointers += 1
                x = x[1:].lstrip()

            while x and x.endswith("*"):
                right_pointers = True
                pointers += 1
                x = x[:-1].rstrip()

            if not x or x == "const":
                continue

            if right_pointers and len(base_type):
                raise ValueError("pointer parsing failure for type '" + ' '.join(fragments) + "'")

            base_type.append(x)

        return cls(' '.join(fragments), ' '.join(base_type), pointers, tags)

class CppArgument:
    def __init__(self, name, type):
        self.name = name
        self.type = type

    @classmethod
    def create(cls, name, fragments, tags):
        return cls(name, CppType.create(fragments, tags))

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

    def get(self):
        return self.line[self.position]

    def back(self): # this can only be called once after calling next().
        self.position -= 1

def parse_comment(grabber: ExportTraverser, tags: list, nested: bool):
    x = grabber.get()
    if x == "/":
        while True:
            if grabber.next() == '\n':
                break

    elif x == "*": 
        x = grabber.next()

        # We're inside a tag-enabled comment at the base nesting level, so we need to parse the tags.
        if x == "*" and not nested:
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
                        grabber.back() # put it back for looping, as it might be a space.
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
        raise ValueError("failed to parse comment at '" + grabber.line + "'")

def parse_cpp_file(path: str, all_functions: dict):
    with open(path, "r") as handle:
        while True:
            line = handle.readline()
            if not line:
                break

            if not export_regex.match(line):
                continue

            grabber = ExportTraverser(handle)

            # Pulling out the result type and name, until the first parenthesis.
            current = ""
            chunks = []
            tags = []
            angle_nesting = 0
            curve_nesting = 0
            funname = None

            while True:
                x = grabber.next()

                if x.isspace():
                    if current:
                        chunks.append(current)
                        current = ""

                elif x == "/":
                    x = grabber.next()

                    # Comments terminate any existing chunk.
                    if x == "/" or x == "*":
                        if current:
                            chunks.append(current)
                            current = ""

                    parse_comment(grabber, tags, curve_nesting or angle_nesting)

                elif x == "<": # deal with templates.
                    angle_nesting += 1
                    current += x

                elif x == ">":
                    if angle_nesting == 0:
                        raise ValueError("imbalanced angle brackets at '" + grabber.line + "'")
                    angle_nesting -= 1
                    current += x

                elif x == "(":
                    if curve_nesting == 0 and angle_nesting == 0:
                        if current == "": # e.g., if there's a space between the name and '('.
                            current = chunks.pop()
                        funname = current
                        break
                    curve_nesting += 1
                    current += x

                elif x == ")":
                    if curve_nesting == 0:
                        raise ValueError("imbalanced parentheses at '" + grabber.line + "'")
                    curve_nesting -= 1
                    current += x

                else:
                    current += x

            restype = CppType.create(chunks, tags)

            # Now pulling out the argument names, until the last (unnested) parenthesis.
            current = ""
            chunks = []
            tags = []
            all_args = []
            angle_nesting = 0
            curve_nesting = 0

            while True:
                x = grabber.next()

                if x.isspace():
                    if curve_nesting or angle_nesting:
                        current += x
                    elif current:
                        chunks.append(current)
                        current = ""

                elif x == "/":
                    x = grabber.next()

                    # Comments terminate any existing chunk.
                    if x == "/" or x == "*":
                        if curve_nesting or angle_nesting:
                            current += x
                        elif current:
                            chunks.append(current)
                            current = ""

                    parse_comment(grabber, tags, curve_nesting or angle_nesting)

                elif x == "<": # deal with templates.
                    angle_nesting += 1
                    current += x

                elif x == ">":
                    if angle_nesting == 0:
                        raise ValueError("imbalanced angle brackets at '" + grabber.line + "'")
                    angle_nesting -= 1
                    current += x

                elif x == "(":
                    curve_nesting += 1
                    current += x

                elif x == ")":
                    if curve_nesting == 0:
                        if angle_nesting != 0:
                            raise ValueError("imbalanced angle brackets at '" + grabber.line + "'")
                        if current == "": # e.g., if there's a space between the final argument name and ')'.
                            current = chunks.pop()
                        all_args.append(CppArgument.create(current, chunks, tags))
                        break
                    curve_nesting -= 1
                    current += x

                elif x== ",":
                    if curve_nesting or angle_nesting:
                        current += x
                    else:
                        if current == "":
                            current = chunks.pop()
                        all_args.append(CppArgument.create(current, chunks, tags))
                        current = ""
                        chunks = []
                        tags = []

                else:
                    current += x

            all_functions[funname] = (restype, all_args)

def parse_cpp_exports(srcdir : str):
    """Parse C++ source files for tagged exports.

    Args:
        srcdir (str): Path to a directory of C++ source files.

    Returns:
        Dict where keys are exported function names and values
        are a tuple of (return type, argument list).
    """
    all_functions = {}
    for p in os.listdir(srcdir):
        if not p.endswith(".cpp"):
            continue
        try: 
            parse_cpp_file(os.path.join(srcdir, p), all_functions)
        except Exception as exc:
            raise ValueError("failed to parse '" + p + "'") from exc
    return all_functions
