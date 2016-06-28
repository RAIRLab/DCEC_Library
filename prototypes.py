"""

"""

from __future__ import print_function
from six import string_types
from six.moves import input  # pylint: disable=locally-disabled,redefined-builtin

import cleaning


class NAMESPACE:
    def __init__(self):
        self.functions = {}
        self.atomics = {}
        self.sorts = {}
        self.quant_map = {"TEMP": 0}

    def add_code_sort(self, name, inheritance=None):
        if inheritance is None:
            inheritance = []
        if not (isinstance(name, string_types) and isinstance(inheritance, list)):
            print("ERROR: function addCodeSort takes arguments of the form, string, "
                  "list of strings")
            return False
        for thing in inheritance:
            if thing not in self.sorts.keys():
                print("ERROR: sort " + thing + " is not previously defined")
                return False
        if name in self.sorts.keys():
            return True
        self.sorts[name] = inheritance
        return True

    def add_text_sort(self, expression):
        temp = expression.replace("(", " ")
        temp = temp.replace(")", " ")
        temp = cleaning.strip_white_space(temp)
        temp = temp.replace("`", "")
        args = temp.split(",")
        if len(args) == 2:
            self.add_code_sort(args[1])
        elif len(args) > 2:
            self.add_code_sort(args[1], args[2:])
        else:
            print("ERROR: Cannot define the sort")
            return False

    def find_atomic_type(self, name):
        if name in self.atomics.keys():
            return self.atomics[name]

    def add_code_function(self, name, return_type, args_types):
        item = [return_type, args_types]
        if name in self.functions.keys():
            if item in self.functions[name]:
                pass
            else:
                self.functions[name].append(item)
        else:
            self.functions[name] = [item]
        return True

    def add_text_function(self, expression):
        temp = expression.replace("(", " ")
        temp = temp.replace(")", " ")
        temp = cleaning.strip_white_space(temp)
        temp = temp.replace("`", "")
        args = temp.split(",")
        if args[0].lower() == "typedef":
            return self.add_text_sort(expression)
        elif len(args) == 2:
            return self.add_text_atomic(expression)
        return_type = ""
        func_name = ""
        func_args = []
        # Find the return type
        if args[0] in self.sorts.keys():
            return_type = args[0]
            args.remove(args[0])
        # Find the function name
        for arg in args:
            if arg not in self.sorts.keys():
                func_name = arg
                args.remove(arg)
                break
        # Find the function args
        for arg in args:
            if arg in self.sorts.keys():
                func_args.append(arg)
        # Error Checking
        if return_type == "" or func_name == "" or func_args == []:
            print("ERROR: The function prototype was not formatted correctly.")
            return False
        # Add the function
        return self.add_code_function(func_name, return_type, func_args)

    def add_code_atomic(self, name, atomic):
        if name in self.atomics.keys():
            if atomic in self.atomics[name]:
                return True
            else:
                print("ERROR: item " + name + " was previously defined as "
                      "an " + self.atomics[name] + ", you cannot overload "
                      "atomics.")
                return False
        else:
            self.atomics[name] = atomic
        return True

    def add_text_atomic(self, expression):
        temp = expression.replace("(", " ")
        temp = temp.replace(")", " ")
        temp = cleaning.strip_white_space(temp)
        temp = temp.replace("`", "")
        args = temp.split(",")
        return_type = ""
        func_name = ""
        # Find the return type
        for arg in args:
            if arg in self.sorts.keys():
                return_type = arg
                args.remove(arg)
                break
        # Find the function name
        for arg in args:
            if arg not in self.sorts.keys():
                func_name = arg
                args.remove(arg)
                break
        return self.add_code_atomic(func_name, return_type)

    def add_basic_dcec(self):
        # The Basic DCEC Sorts
        self.add_code_sort("Object")
        self.add_code_sort("Agent", ["Object"])
        self.add_code_sort("Self", ["Object", "Agent"])
        self.add_code_sort("ActionType", ["Object"])
        self.add_code_sort("Event", ["Object"])
        self.add_code_sort("Action", ["Object", "Event"])
        self.add_code_sort("Moment", ["Object"])
        self.add_code_sort("Boolean", ["Object"])
        self.add_code_sort("Fluent", ["Object"])
        self.add_code_sort("Numeric", ["Object"])
        self.add_code_sort("Set", ["Object"])

        # The Basic DCEC Modal Functions
        self.add_code_function("C", "Boolean", ["Moment", "Boolean"])
        self.add_code_function("B", "Boolean", ["Agent", "Moment", "Boolean"])
        self.add_code_function("K", "Boolean", ["Agent", "Moment", "Boolean"])
        self.add_code_function("P", "Boolean", ["Agent", "Moment", "Boolean"])
        self.add_code_function("I", "Boolean", ["Agent", "Moment", "Boolean"])
        self.add_code_function("D", "Boolean", ["Agent", "Moment", "Boolean"])
        self.add_code_function("S", "Boolean", ["Agent", "Agent", "Moment", "Boolean"])
        self.add_code_function("O", "Boolean", ["Agent", "Moment", "Boolean", "Boolean"])

        # Fluent Functions
        self.add_code_function("action", "Action", ["Agent", "ActionType"])
        self.add_code_function("initially", "Boolean", ["Fluent"])
        self.add_code_function("holds", "Boolean", ["Fluent", "Moment"])
        self.add_code_function("happens", "Boolean", ["Event", "Moment"])
        self.add_code_function("clipped", "Boolean", ["Moment", "Fluent", "Moment"])
        self.add_code_function("initiates", "Boolean", ["Event", "Fluent", "Moment"])
        self.add_code_function("terminates", "Boolean", ["Event", "Fluent", "Moment"])
        self.add_code_function("prior", "Boolean", ["Moment", "Moment"])
        self.add_code_function("interval", "Fluent", ["Moment", "Boolean"])
        self.add_code_function("self", "Self", ["Agent"])
        self.add_code_function("payoff", "Numeric", ["Agent", "ActionType", "Moment"])

        # Logical Functions
        self.add_code_function("implies", "Boolean", ["Boolean", "Boolean"])
        self.add_code_function("iff", "Boolean", ["Boolean", "Boolean"])
        self.add_code_function("not", "Boolean", ["Boolean"])
        self.add_code_function("and", "Boolean", ["Boolean", "Boolean"])

        # Time Functions
        self.add_code_function("lessOrEqual", "Boolean", ["Moment", "Moment"])

    def add_basic_logic(self):
        # Logical Functions
        self.add_code_function("or", "Boolean", ["Boolean", "Boolean"])
        self.add_code_function("xor", "Boolean", ["Boolean", "Boolean"])

    def add_basic_numerics(self):
        # Numerical Functions
        self.add_code_function("negate", "Numeric", ["Numeric"])
        self.add_code_function("add", "Numeric", ["Numeric", "Numeric"])
        self.add_code_function("sub", "Numeric", ["Numeric", "Numeric"])
        self.add_code_function("multiply", "Numeric", ["Numeric", "Numeric"])
        self.add_code_function("divide", "Numeric", ["Numeric", "Numeric"])
        self.add_code_function("exponent", "Numeric", ["Numeric", "Numeric"])

        # Comparison Functions
        self.add_code_function("greater", "Boolean", ["Numeric", "Numeric"])
        self.add_code_function("greaterOrEqual", "Boolean", ["Numeric", "Numeric"])
        self.add_code_function("less", "Boolean", ["Numeric", "Numeric"])
        self.add_code_function("lessOrEqual", "Boolean", ["Numeric", "Numeric"])
        self.add_code_function("equals", "Boolean", ["Numeric", "Numeric"])

    def no_conflict(self, type1, type2, level):
        if type1 == "?":
            return True, level
        elif type1 == type2:
            return True, level
        elif type2 in self.sorts[type1]:
            return True, level + 1
        else:
            returnlist = []
            for i in self.sorts[type1]:
                recurse_return = self.no_conflict(i, type2, level + 1)
                if recurse_return[0]:
                    returnlist.append([recurse_return[1]])
            if len(returnlist) > 0:
                return True, min(returnlist)[0]
            else:
                return False, level

    def print_namespace(self):
        for item in self.sorts.keys():
            print(item, self.sorts[item])
        for item in self.functions:
            print(item, self.functions[item])
        for item in self.atomics:
            print(item, self.atomics[item])


if __name__ == "__main__":
    THIS = NAMESPACE()
    EXPRESSION = input("Enter Prototype: ")
    THIS.add_text_function(EXPRESSION)
    THIS.add_basic_dcec()
    THIS.print_namespace()
