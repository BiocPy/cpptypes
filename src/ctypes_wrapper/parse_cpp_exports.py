import os
import re

export_regex = re.compile("^// *\\[\\[export\\]\\]")
comment_regex = re.compile("//")


class CppType:
    def __init__(self, full_type, base_type, pointer_level, tags):
        self.full_type = full_type
        self.base_type = base_type
        self.pointer_level = pointer_level
        self.tags = set(tags)

    @classmethod
    def create(cls, full_type):
        # Parsing out the inline comments, which might contain tags.
        bits = ""
        i = 0
        last = 0
        N = len(full_type)
        tags = []

        while i < N:
            if full_type[i] == "/" and full_type[i + 1] == "*":
                bits += full_type[last:i]
                i += 2
                start = i
                terminated = False

                while i + 1 < N:
                    if full_type[i] == "*" and full_type[i + 1] == "/":
                        terminated = True
                        break
                    i += 1

                if not terminated:
                    raise ValueError("unterminated comment in type '" + full_type + "'")

                if full_type[start] == "*":
                    tagset = full_type[start + 1 : i]
                    tags += tagset.split()

                i += 2
                last = i
            else:
                i += 1

        bits += full_type[last:i]

        # Now deconvolving the remaining bits and pieces.
        fragments = bits.split()
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
                raise ValueError("pointer parsing failure for type '" + full_type + "'")

            base_type.append(x)

        return cls(full_type, " ".join(base_type), pointers, tags)


class CppArgument:
    def __init__(self, name, type):
        self.name = name
        self.type = type

    @classmethod
    def create(cls, name, full_type):
        return cls(name, CppType.create(full_type))


def parse_cpp_exports(srcdir: str):
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

        with open(os.path.join(srcdir, p), "r") as handle:
            capture = False
            combined = ""

            for line in handle:
                if export_regex.match(line):
                    capture = True
                    combined = ""

                elif capture:
                    # Remove comments.
                    comment_found = comment_regex.search(line)
                    if comment_found:
                        line = line[: comment_found.pos]

                    combined += line.strip()
                    if line.find("{") != -1:
                        first_bracket = combined.find("(")
                        first_space = combined.rfind(" ", 0, first_bracket)
                        restype = combined[:first_space].strip()
                        funname = combined[first_space + 1 : first_bracket].strip()

                        last_bracket = combined.rfind(")")
                        template_nesting = 0
                        last_arg = first_bracket
                        args = []
                        for i in range(first_bracket + 1, last_bracket):
                            if combined[i] == "<":
                                template_nesting += 1
                            elif combined[i] == ">":
                                template_nesting -= 1
                            elif combined[i] == ",":
                                if template_nesting == 0:
                                    curarg = combined[last_arg + 1 : i].strip()
                                    argname_start = max(
                                        curarg.rfind(" "),
                                        curarg.rfind("*"),
                                        curarg.rfind("&"),
                                    )
                                    args.append(
                                        CppArgument.create(
                                            curarg[argname_start + 1 :].strip(),
                                            curarg[:argname_start].strip(),
                                        )
                                    )
                                    last_arg = i

                        curarg = combined[last_arg + 1 : last_bracket].strip()
                        argname_start = max(
                            curarg.rfind(" "), curarg.rfind("*"), curarg.rfind("&")
                        )
                        args.append(
                            CppArgument.create(
                                curarg[argname_start + 1 :].strip(),
                                curarg[:argname_start].strip(),
                            )
                        )

                        all_functions[funname] = (CppType.create(restype), args)
                        capture = False

    return all_functions
