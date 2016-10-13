from __future__ import print_function
from six import string_types
from six.moves import input  # pylint: disable=locally-disabled,redefined-builtin

# We need to use the first type of import if running this script directly and the second type of
# import if we're using it in a package (such as for within Talos)
try:
    import prototypes
    import cleaning
except ImportError:
    import DCEC_Library.prototypes as prototypes
    import DCEC_Library.cleaning as cleaning


class Token:
    """
    Parsed representation of a formal logic statement given its function name and then
    a list of arguments that make up the Token. We then use this for parsing as well as
    for displaying representations of the formula in S and F form.
    """
    def __init__(self, funcname, args):
        self.function_name = funcname
        self.args = args
        self.depth = None
        self.width = None
        self.s_expression = None
        self.f_expression = None

    def depth_of(self):
        """
        Get the max depth of this token where a token represents one depth, thus for each
        token contained as an argument, you go down one more level of depth

        :return: max depth of token
        """
        temp = []
        for arg in self.args:
            if isinstance(arg, Token):
                temp.append(arg)
        if len(temp) == 0:
            self.depth = 1
        else:
            self.depth = 1+max([x.depth_of() for x in temp])
        return self.depth

    def width_of(self):
        """
        Get the width of the token which represents the number of children the token and its
        subsequent token children have

        :return: width of token
        """
        temp = 0
        for arg in self.args:
            if isinstance(arg, string_types):
                temp += 1
            else:
                temp += arg.width_of()
        self.width = temp
        return self.width

    def create_s_expression(self):
        """
        Recursively create the S expression for this token. S expressions are of the
        form (func_name arg1 arg2) where args could then be additional S expressions

        :return: S expression representing this token
        """
        self.s_expression = "(" + self.function_name + " "
        for arg in self.args:
            if isinstance(arg, string_types):
                self.s_expression += arg + " "
            else:
                arg.create_s_expression()
                self.s_expression += arg.s_expression + " "
        self.s_expression = self.s_expression.strip()
        self.s_expression += ")"
        return self.s_expression

    def create_f_expression(self):
        """
        Recursively create the F(unctional) expression for this token. F expressions are
        of the form func_name(arg1, arg2) where args could be additional F expressions

        :return: F expression representing this token
        """
        self.f_expression = self.function_name + "("
        for arg in self.args:
            if isinstance(arg, string_types):
                self.f_expression += arg + ","
            else:
                arg.create_f_expression()
                self.f_expression += arg.f_expression + ","
        self.f_expression = self.f_expression.strip(",")
        self.f_expression += ")"
        return self.f_expression

    def print_tree(self):
        """
        Generate the S and F expression for the token, then print the F expression out
        """
        self.create_s_expression()
        self.create_f_expression()
        print(self.f_expression)


def remove_comments(expression):
    """
    Remove any comments from an expression. This is defined as anything after a ';' mark in the
    expression

    :param expression: expression to remove comments from
    :return: parsed expression without comments
    """
    index = expression.find(";")
    if index != -1:
        expression = expression[:index]
    if len(expression) == 0:
        expression = ""
    return expression


def functorize_symbols(expression):
    """
    This function replaces all symbols with the appropreate internal funciton name.
    Some symbols are left untouched, these symbols have multiple interpretations in the DCEC
    syntax. For example, the symbol * can represent both multiplication and the self operator.
    """
    symbols = ["^", "*", "/", "+", "<->", "->", "-", "&", "|", "~", ">=", "==", "<=", "===", "=",
               ">", "<"]
    symbol_map = {
        "^": "exponent",
        "*": "*",
        "/": "divide",
        "+": "add",
        "-": "-",
        "&": "&",
        "|": "|",
        "~": "not",
        "->": "implies",
        "<->": "ifAndOnlyIf",
        ">": "greater",
        "<": "less",
        ">=": "greaterOrEqual",
        "<=": "lessOrEqual",
        "=": "equals",
        "==": "equals",
        "===": "tautology",
    }
    returner = expression
    for symbol in symbols:
        returner = returner.replace(symbol, " " + symbol_map[symbol] + " ")
    returner = returner.replace("( ", "(")
    return returner


def replace_synonyms(args):
    """
    These are some common spelling errors that users demand the parser takes
    care of, even though it increases "shot-in-foot" syndrome.

    >>> replace_synonyms(["ifAndOnlyIf", "if", "iff", "Time", "forall", "Forall", "ForAll", \
    "Exists"])
    WARNING: replaced the common mispelling ifAndOnlyIf with the correct name of iff
    WARNING: replaced the common mispelling if with the correct name of implies
    WARNING: replaced the common mispelling Time with the correct name of Moment
    WARNING: replaced the common mispelling forall with the correct name of forAll
    WARNING: replaced the common mispelling Forall with the correct name of forAll
    WARNING: replaced the common mispelling ForAll with the correct name of forAll
    WARNING: replaced the common mispelling Exists with the correct name of exists
    ['iff', 'implies', 'iff', 'Moment', 'forAll', 'forAll', 'forAll', 'exists']
    >>> replace_synonyms("if")
    WARNING: replaced the common mispelling if with the correct name of implies
    'implies'

    :param args: either a list of arguments to convert or a string to convert based on synomyn map
    :return: parsed args that has all common mispellings replaced
    """
    synonym_map = {
        "ifAndOnlyIf": "iff",
        "if": "implies",
        "Time": "Moment",
        "forall": "forAll",
        "Forall": "forAll",
        "ForAll": "forAll",
        "Exists": "exists",
    }
    if not isinstance(args, list):
        args = str(args)
        if args in synonym_map:
            print("WARNING: replaced the common mispelling %s with the correct name of %s" %
                  (args, synonym_map[args]))
            args = synonym_map[args]
    else:
        args = [str(arg) for arg in args]
        for arg in range(0, len(args)):
            if args[arg] in synonym_map:
                print("WARNING: replaced the common mispelling %s with the correct "
                      "name of %s" % (args[arg], synonym_map[args[arg]]))
                args[arg] = synonym_map[args[arg]]
    return args


def prefix_logical_functions(args, add_atomics):
    """
    This function turns infix notation into prefix notation. It assumes standard
    logical order of operations.
    """
    logic_keywords = ["not", "and", "or", "xor", "implies", "iff"]
    # Checks for infix notation
    if len(args) < 3:
        return args
    # Checks for infix notation. Order of operations is only needed in infix notation.
    if not args[-2] in logic_keywords:
        return args
    # This is a very common error. Order of operations really fucks with the parser, especially
    # because it needs to interpret both S and F notations. Because of this, operations are read
    # left-to-right throughout the parser.
    for arg in range(0, len(args)):
        if args[arg] == "not" and arg+2 < len(args) and not args[arg+1] in logic_keywords:
            print("WARNING: ambiguous not statement. This parser assumes standard order of "
                  "logical operations. Please use prefix notation or parentheses to resolve "
                  "this ambiguity.")
    for word in logic_keywords:
        while word in args:
            index = args.index(word)
            if word == "not":
                new_token = Token(word, [args[index+1]])
                # Assign sorts to the atomics used
                if args[index+1] in add_atomics.keys():
                    add_atomics[args[index + 1]].append("Boolean")
                else:
                    add_atomics[args[index + 1]] = ["Boolean"]
                # Replace infix notation with tokenized representation
                args = args[:index+1]+args[index+2:]
                args[index] = new_token
                break
            in1 = index-1
            in2 = index+1
            # If the thing is actually prefix anyway > twitch <
            if in1 < 0:
                break
            # Tucks the arithmetic expression into a token
            new_token = Token(word, [args[in1], args[in2]])
            # Assign sorts to the atomics used
            if args[in1] in add_atomics.keys():
                add_atomics[args[in1]].append("Boolean")
            else:
                add_atomics[args[in1]] = ["Boolean"]
            if args[in2] in add_atomics.keys():
                add_atomics[args[in2]].append("Boolean")
            else:
                add_atomics[args[in2]] = ["Boolean"]
            # Replace the args used in the token with the token
            args = args[:in1]+args[in2:]
            args[in1] = new_token
    return args


def prefix_emdas(args, add_atomics):
    """
    This function turns infix notation into a tokenized prefix notation using the standard
    PEMDAS order of operations.
    """
    arithmetic_keywords = ["negate", "exponent", "multiply", "divide", "add", "sub"]
    # Checks for infix notation
    if len(args) < 3:
        return args
    # Checks for infix notation. PEMDAS is only needed in infix notation.
    elif not args[-2] in arithmetic_keywords:
        return args
    else:
        pass
    for word in arithmetic_keywords:
        while word in args:
            index = args.index(word)
            if word == "negate":
                new_token = Token(word, [args[index+1]])
                # Assign sorts to the atomics used
                if args[index+1] in add_atomics.keys():
                    add_atomics[args[index + 1]].append("Numeric")
                else:
                    add_atomics[args[index + 1]] = ["Numeric"]
                # Replace infix notation with tokenized representation
                args = args[:index+1]+args[index+2:]
                args[index] = new_token
                continue
            in1 = index-1
            in2 = index+1
            # If it mixes both forms > twitch <
            if in1 < 0:
                break
            # Tucks the arithmetic expression into a token
            new_token = Token(word, [args[in1], args[in2]])
            # Assign sorts to the atomics used
            if args[in1] in add_atomics.keys():
                add_atomics[args[in1]].append("Numeric")
            else:
                add_atomics[args[in1]] = ["Numeric"]
            if args[in2] in add_atomics.keys():
                add_atomics[args[in2]].append("Numeric")
            else:
                add_atomics[args[in2]] = ["Numeric"]
            # Replace the args used in the token with the token
            args = args[:in1] + args[in2:]
            args[in1] = new_token
    return args


def assign_types(args, namespace, add_atomics, add_functions):
    """
    This function assigns sorts to atomics, tokens, and inline defined functions based
    on the sorts keywords.
    """
    # Add the types to the namespace
    for arg in range(0, len(args)):
        if args[arg] in namespace.sorts.keys():
            if arg+1 == len(args):
                print("ERROR: Cannot find something to attach the sort \""+args[arg]+"\". "
                      "Cannot overload sorts.")
                return False
            elif args[arg+1] in namespace.sorts.keys() or \
                            args[arg+1] in namespace.functions.keys():
                print("ERROR: Cannot assign inline types to basicTypes, keywords, or function "
                      "names")
                return False
            elif isinstance(args[arg+1], Token):
                name = args[arg+1].funcName
                inargs = []
                for x in args[arg+1].args:
                    if x in namespace.atomics.keys():
                        inargs.append(namespace.atomics[x])
                    elif x in add_atomics.keys():
                        inargs.append(add_atomics[x][0])
                    else:
                        print("ERROR: token \""+str(x)+"\" has an unknown type. Please type it.")
                        return False
                if name in add_functions.keys():
                    for item in add_functions[name]:
                        if inargs == item[1]:
                            if item[0] == "?":
                                item[0] = args[arg]
                            elif item[0] == args[arg]:
                                continue
                            else:
                                print("ERROR: A function cannot have two different returntypes")
                                return False
                        else:
                            new_item = [name, inargs]
                            if name in add_functions.keys():
                                add_functions[name].append(new_item)
                            else:
                                add_functions[name] = [new_item]
            else:
                add_atomics[args[arg + 1]] = [args[arg]]
    # Remove the types from the expression
    counter = 0
    while counter != len(args):
        if args[counter] in namespace.sorts.keys():
            args.pop(counter)
            continue
        else:
            counter += 1
    return True


def distinguish_functions(args, namespace, add_atomics, add_functions):
    """
    Because several symbols in the DCEC syntax can mean more than one thing, this
    function tries to resolve that ambiguity by looking at various sorts.
    Hopefully, users do not use these symbols and instead use the unambiguous names
    instead.
    """
    if len(args) == 1:
        return True
    for arg in range(0, len(args)):
        if args[arg] == "*":
            # CAN ADD HEURISTIC THAT SELF HAS ONE ARG AND MULTIPLY HAS 2 HERE
            if arg == 0:
                args[arg] = "multiply"
            elif args[arg-1] == "self":
                args[arg] = args[arg-1]
                args[arg-1] = "self"
            elif args[arg-1] in namespace.atomics.keys():
                if namespace.atomics[args[arg-1]] == "Agent":
                    args[arg] = args[arg-1]
                    args[arg-1] = "self"
                elif namespace.atomics[args[arg-1]] == "Numeric":
                    args[arg] = "multiply"
                else:
                    print("ERROR: keyword * does not take atomic arguments of type: " +
                          namespace.atomics[args[arg-1]])
                    return False
            elif args[arg-1] in add_atomics.keys():
                if add_atomics[args[arg-1]][0] == "Agent":
                    args[arg] = args[arg-1]
                    args[arg-1] = "self"
                elif add_atomics[args[arg-1]][0] == "Numeric":
                    args[arg] = "multiply"
                else:
                    print("ERROR: keyword * does not take atomic arguments of type: " +
                          add_atomics[args[arg - 1]][0])
                    return False
            else:
                print("ERROR: ambiguous keyword * can be either self or multiply, please set the "
                      "types of your atomics and use parentheses.")
                return False
        if args[arg] == "-":
            if arg == 0:
                args[arg] = "negate"
            elif args[arg-1] in namespace.atomics.keys():
                if namespace.atomics[args[arg-1]] != "Numeric":
                    args[arg] = "negate"
                elif len(args) > arg+1 and args[arg+1] in namespace.atomics.keys():
                    if namespace.atomics[args[arg+1]] != "Numeric":
                        print("ERROR: - keyword does not take " + namespace.atomics[args[arg+1]] +
                              " arguments.")
                        return False
                    else:
                        args[arg] = "sub"
            elif args[arg-1] in add_atomics.keys():
                if add_atomics[args[arg-1]][0] != "Numeric":
                    args[arg] = "negate"
                elif len(args) > arg+1 and args[arg+1] in add_atomics.keys():
                    if add_atomics[args[arg+1]][0] != "Numeric":
                        print("ERROR: - keyword does not take " + add_atomics[args[arg + 1]][0] +
                              " arguments.")
                        return False
                    else:
                        args[arg] = "sub"
            elif args[arg-1] in namespace.functions.keys():
                args[arg] = "negate"
            elif args[arg-1] in add_functions.keys():
                args[arg] = "negate"
            else:
                print("ERROR: keyword - can be either sub or negate, please add types, or use "
                      "the sub or negate keywords")
                return False
        if args[arg] == "&":
            if arg+1 < len(args) and args[arg+1] in namespace.atomics.keys():
                if namespace.atomics[args[arg+1]] == "Boolean":
                    args[arg] = "and"
                elif namespace.atomics[args[arg+1]] == "Set":
                    args[arg] = "union"
                else:
                    print("ERROR: keyword & does not take "+namespace.atomics[args[arg+1]] +
                          " arguments")
                    return False
            elif arg+1 < len(args) and args[arg+1] in add_atomics.keys():
                if add_atomics[args[arg+1]][0] == "Boolean":
                    args[arg] = "and"
                elif add_atomics[args[arg+1]][0] == "Set":
                    args[arg] = "union"
                else:
                    print("ERROR: keyword & does not take " + add_atomics[args[arg + 1]][0] +
                          " arguments")
                    return False
            else:
                print("ERROR: keyword & can be either union or and, please add types, or use the "
                      "and or union keyword.")
                return False
        if args[arg] == "|":
            if arg+1 < len(args) and args[arg+1] in namespace.atomics.keys():
                if namespace.atomics[args[arg+1]] == "Boolean":
                    args[arg] = "or"
                elif namespace.atomics[args[arg+1]] == "Set":
                    args[arg] = "intersection"
                else:
                    print("ERROR: keyword | does not take "+namespace.atomics[args[arg+1]] +
                          " arguments")
                    return False
            elif arg+1 < len(args) and args[arg+1] in add_atomics.keys():
                if add_atomics[args[arg+1]][0] == "Boolean":
                    args[arg] = "or"
                elif add_atomics[args[arg+1]][0] == "Set":
                    args[arg] = "intersection"
                else:
                    print("ERROR: keyword | does not take " + add_atomics[args[arg + 1]][0] +
                          " arguments")
                    return False
            else:
                print("ERROR: keyword | can be either union or and, please add types, or "
                      "use the or or intersect keyword.")
                return False
    return True


def check_prenex(args, add_quants):
    for arg in args:
        if arg in add_quants.keys() and 'QUANT' not in arg:
            print("WARNING: not using prenex form. This may cause an error if improperly handled. "
                  "Use prenex form and make sure that your quantifiers are unique.")


def next_internal(namespace):
    if "TEMP" not in namespace.quant_map.keys():
        namespace.quant_map["TEMP"] = 0
        nextnumber = 0
    else:
        nextnumber = namespace.quant_map["TEMP"]
        namespace.quant_map["TEMP"] += 1
    nextinternal = 'QUANT'+str(nextnumber)
    if nextinternal in namespace.atomics:
        return next_internal(namespace)
    else:
        return nextinternal


def pop_quantifiers(args, highlevel, sublevel, namespace, quantifiers, add_quants,
                    add_atomics):
    """
    This function removes all quantifiers from the statement, and replaces quantified variables
    with thier internal representations. These representations are then stored in the namespace
    atomics map.
    """
    removelist = []
    place = 0
    for arg in range(0, len(args)):
        # Replace quants with internal representations
        if args[arg] in add_quants.keys():
            args[arg] = add_quants[args[arg]]
        # Hey look here is a quantifier
        if args[arg] in ["forAll", "exists"]:
            # Move to the next argument
            arg += 1
            # Check for args in parens
            if args[arg] == "":
                removelist.append(arg-1)
                removelist.append(arg)
                new_args = highlevel[sublevel[0][0]:sublevel[0][1]][1:-1].split(",")
                place += 1
                interned = next_internal(namespace)
                for temp in new_args:
                    if temp in namespace.sorts.keys():
                        add_atomics[interned] = [temp]
                        continue
                    else:
                        add_quants[interned] = temp
                        add_quants[temp] = interned
                        quantifiers.append(args[arg-1])
                        quantifiers.append(interned)
                        interned = next_internal(namespace)
            # if the quantifier is written as forAll x forAll y forAll z blah(x,y,z)
            elif isinstance(args[arg], Token) or "[" not in args[arg]:
                removelist.append(arg-1)
                removelist.append(arg)
                interned = next_internal(namespace)
                if args[arg] in namespace.sorts.keys():
                    add_atomics[interned] = [args[arg]]
                    arg += 1
                    removelist.append(arg)
                add_quants[interned] = args[arg]
                add_quants[args[arg]] = interned
                quantifiers.append(args[arg-1])
                quantifiers.append(interned)
            # If the quantifier is written with a list of symbols ex. forAll [x,y,z] blah(x,y,z)
            else:
                # Store the quant type
                temp_quant = args[arg-1]
                removelist.append(arg-1)
                while True:
                    new_arg = args[arg].strip("[").strip("]")
                    args[arg] = args[arg].strip("[")
                    removelist.append(arg)
                    interned = next_internal(namespace)
                    if new_arg in namespace.sorts.keys():
                        add_atomics[interned] = [new_arg]
                        arg += 1
                        removelist.append(arg)
                        new_arg = args[arg].strip("[").strip("]")
                    add_quants[interned] = new_arg
                    add_quants[new_arg] = interned
                    quantifiers.append(temp_quant)
                    quantifiers.append(interned)
                    arg += 1
                    if "]" in args[arg-1]:
                        args[arg-1] = args[arg-1].strip("]")
                        break
    # Remove quantifiers from the arguments
    args = [i for j, i in enumerate(args) if j not in removelist]
    return args, place


def assign_args(func_name, args, namespace, add_atomics, add_functions):
    """
    This function attempts to assign sorts to the current function and all of its arguments.
    It also attempts to differentiate between different overloaded functions.
    """
    # Fluents are weird, this is as good as it gets
    fluents = ["action", "initially", "holds", "happens", "clipped", "initiates", "terminates",
               "prior", "interval", "self", "payoff"]
    exceptions = []
    # This is more sane. Find the right set of arguments for overloaded functions.
    temp_args = args
    temp_args.remove(func_name)
    real_types = []
    arg = 0
    # TODO: by assigning namespace.atomics and add_atomics to a variable, we should be able to
    # condense this code as it's very duplicated (or use a function?)
    if func_name in namespace.functions.keys():
        while arg < len(temp_args) and \
                        arg < max([len(x[1]) for x in namespace.functions[func_name]]):
            if temp_args[arg] in namespace.atomics.keys():
                real_types.append(namespace.atomics[temp_args[arg]])
            elif temp_args[arg] in namespace.functions.keys():
                if temp_args[arg] in fluents:
                    exceptions.append(len(real_types))
                new_tail, return_type = assign_args(temp_args[arg], temp_args[arg:], namespace,
                                                    add_atomics, add_functions)
                real_types.append(return_type)
                temp_args = temp_args[:arg]+new_tail
            elif temp_args[arg] in add_atomics.keys():
                real_types.append(add_atomics[temp_args[arg]][0])
            else:
                real_types.append("?")
            arg += 1
    else:
        while arg < len(temp_args) and arg < max([len(x[1]) for x in add_functions[func_name]]):
            if temp_args[arg] in add_atomics.keys():
                real_types.append(add_atomics[temp_args[arg]][0])
            elif temp_args[arg] in namespace.functions.keys():
                if temp_args[arg] in fluents:
                    exceptions.append(len(real_types))
                new_tail, return_type = assign_args(temp_args[arg], temp_args[arg:], namespace,
                                                    add_atomics, add_functions)
                real_types.append(return_type)
                temp_args = temp_args[:arg]+new_tail
            elif temp_args[arg] in add_functions.keys():
                if temp_args[arg] in fluents:
                    exceptions.append(len(real_types))
                new_tail, return_type = assign_args(temp_args[arg], temp_args[arg:], namespace,
                                                    add_atomics, add_functions)
                real_types.append(return_type)
                temp_args = temp_args[:arg]+new_tail
            else:
                real_types.append("?")
            arg += 1
    valid_items = []
    # Find the right item
    if func_name in namespace.functions.keys():
        for item in namespace.functions[func_name]:
            valid = True
            levels = []
            if not len(item[1]) <= len(real_types):
                continue
            for arg in range(0, len(item[1])):
                returnthing = namespace.no_conflict(real_types[arg], item[1][arg], 0)
                if returnthing[0]:
                    levels.append(returnthing[1])
                # Fluents are special, they can take bools, ect.
                elif item[1][arg] == "Fluent":
                    if arg in exceptions:
                        pass
                    else:
                        valid = False
                        break
                else:
                    valid = False
                    break
            if valid:
                valid_items.append([item, levels])
    if func_name in add_functions.keys():
        for item in add_functions[func_name]:
            valid = True
            levels = []
            if not len(item[1]) <= len(real_types):
                continue
            for arg in range(0, len(item[1])):
                returnthing = namespace.no_conflict(real_types[arg], item[1][arg], 0)
                if returnthing[0]:
                    levels.append(returnthing[1])
                # Fluents are special, they can take bools, etc
                elif item[1][arg] == "Fluent":
                    if arg in exceptions:
                        pass
                    else:
                        valid = False
                        break
                else:
                    valid = False
                    break
            if valid:
                valid_items.append([item, levels])
    if len(valid_items) > 1:
        # Sort by length first
        sorted_items = sorted(valid_items, key=lambda item: len(item[1]), reverse=True)
        if len(sorted_items[0][1]) == len(sorted_items[1][1]):
            sorted_items = sorted(valid_items, key=lambda item: sum(item[1]))
            if sum(sorted_items[0][1]) == sum(sorted_items[1][1]):
                print("ERROR: more than one possible interpretation for function \"" + func_name +
                      "\". Please type your atomics.")
                print("   The interpretations are:")
                for i in sorted_items:
                    print("interpretation: ", i[0], " Constraining factor: ", sum(i[1]))
                print("   you gave:")
                print("  ", real_types)
                return False, []
            else:
                valid_items = [sorted_items[0]]
        else:
            valid_items = [sorted_items[0]]
    elif len(valid_items) == 0:
        print("ERROR: the function named \"" + func_name + "\" does not take arguments of the type "
              "provided. You cannot overload inline. Use prototypes.")
        print("   the possible inputs for \"" + func_name + "\" are:")
        # Print the possible interpretations
        if func_name in namespace.functions.keys():
            for i in namespace.functions[func_name]:
                print("  ", i[1])
        if func_name in add_functions.keys():
            for i in add_functions[func_name]:
                print("  ", i[1])
        print("   you gave:")
        print("  ", real_types)
        # Throw an error
        return False, []
    # Assign Types
    valid_items = [valid_items[0][0]]
    for arg in range(0, len(valid_items[0][1])):
        if temp_args[arg] in add_atomics.keys():
            add_atomics[temp_args[arg]].append(valid_items[0][1][arg])
        else:
            add_atomics[temp_args[arg]] = [valid_items[0][1][arg]]
    # Make a token of the right function
    new_token = Token(func_name, temp_args[:len(valid_items[0][1])])
    add_atomics[new_token] = [valid_items[0][0]]
    # Remove used args from list:
    return_args = [new_token]
    return_args += temp_args[len(valid_items[0][1]):]
    return return_args, add_atomics[new_token][0]


def token_tree(expression, namespace, quantifiers, add_quants, add_atomics, add_functions):
    """
    This is the meat and potatoes function of the parser. It pulls together all of the
    other utility functions and decides which words are function names, which are
    arguments to the functions, and which are special keywords that define sorts, ect.
    Most of the complexity of the parser comes from dealing with overloaded and inline
    functions. Unfortunately, the users demand these features, so the parser must make
    it easy to shoot oneself in the foot with it.
    """
    # Strip the outer parens
    temp = expression[1:-1].strip(",")
    # check for an empty string
    if temp == "":
        return temp
    # Find the sub-level tokens at this level of parsing
    level = 0
    highlevel = ""
    sublevel = []
    for index in range(0, len(temp)):
        if temp[index] == "(":
            level += 1
            if level == 1:
                sublevel.append([index, cleaning.get_matching_close_paren(temp, index) + 1])
            continue
        if temp[index] == ")":
            level -= 1
            continue
        if level == 0:
            highlevel = highlevel + temp[index]
    # These are the function components. One is the function name, the others are its args.
    args = highlevel.split(",")   
    place = 0
    # Fix some common keyword mistakes
    replace_synonyms(args)
    if isinstance(args, bool):
        return False
    # Rip out quantified statements
    args, offset = pop_quantifiers(args, temp, sublevel, namespace, quantifiers, add_quants,
                                   add_atomics)
    place += offset
    if isinstance(args, bool):
        return False
    # Tokens can be nested, so this recurses thorough the tree
    for index in range(0, len(args)):
        if args[index] == "":
            args[index] = token_tree(temp[sublevel[place][0]:sublevel[place][1]], namespace,
                                     quantifiers, add_quants, add_atomics, add_functions)
            if not args[index]:
                return False
            place += 1
    # Assign inline types
    if not assign_types(args, namespace, add_atomics, add_functions):
        return False
    # Distinguish inbetween ambiguous symbols
    if not distinguish_functions(args, namespace, add_atomics, add_functions):
        return False
    # Check for prenex form
    check_prenex(args, add_quants)
    # Prefix inline logical functions
    args = prefix_logical_functions(args, add_atomics)
    # Prefix inline numeric functions
    args = prefix_emdas(args, add_atomics)
    # If this is a basic argument, it does not need to be tokenized
    if len(args) == 1:
        return args[0]
    # Otherwise it does, more than one arg means one is a function name and others are args
    while len(args) > 1:
        # Find the function name. If a function is known this will find it.
        primary_token = ""
        for arg in args:
            if arg in namespace.functions.keys():
                primary_token = arg
                break
            elif arg in add_functions.keys():
                primary_token = arg
                break
        # If there is no primary token, the first arg is a function (this will only happen in an
        # inline function definition)
        if primary_token == "":
            primary_token = args[0]
            # Check if there is no function name. This will happen in postfix notation or if the
            # user is bad. We do not support this
            if isinstance(primary_token, Token):
                print("ERROR: \"" + primary_token.create_s_expression() + "\" is not a valid "
                      "function name. Postfix notation is not supported when defining inline "
                      "functions.")
                return False
            # Attempt to define the inline function
            sub_types = []
            for arg in args[1:]:
                if arg in namespace.atomics.keys():
                    sub_types.append(namespace.atomics[arg])
                elif arg in add_atomics.keys():
                    sub_types.append(add_atomics[arg][0])
                else:
                    print("ERROR: token \""+str(arg)+"\" is of an unknown type. Please type it.")
                    return False
            new_token = Token(primary_token, args[1:])
            if primary_token in add_functions.keys():
                # This is a very common error, but unfortunately cannot be let go without a
                # warning. Inline functions need to be defined outside of the parentheses, but
                # most people are too lazy. However, some people might forget a paren or name or
                # something which would lead to the same syntax as the previous case, but
                # unintentionally. This makes this conditional ambiguous, but because the
                # alternative results in an error, the parser will assume that the user meant for
                # this to happen.
                if primary_token in add_atomics.keys():
                    add_functions[primary_token].append([add_atomics[primary_token][0], sub_types])
                    print("WARNING: ambiguity in parsing. Assuming that the inline function \"%s\""
                          " has returntype of %s. Please place inline return type definitions "
                          "outside of the function definition, or use prototypes."
                          % (primary_token, add_atomics[primary_token][0]))
                    del add_atomics[primary_token]
                else:
                    add_functions[primary_token].append(["?", sub_types])
            # This is a very common error, but unfortunately cannot be let go without a warning.
            # Inline functions need to be defined outside of the parentheses, but most people are
            # too lazy. However, some people might forget a paren or name or something which would
            # lead to the same syntax as the previous case, but unintentionally. This makes this
            # conditional ambiguous, but because the alternative results in an error, the parser
            # will assume that the user meant for this to happen.
            elif primary_token in add_atomics.keys():
                add_functions[primary_token] = [[add_atomics[primary_token][0], sub_types]]
                print("WARNING: ambiguity in parsing. Assuming that the inline function \"%s\""
                      " has returntype of %s. Please place inline return type definitions "
                      "outside of the function definition, or use prototypes."
                      % (primary_token, add_atomics[primary_token][0]))
                del add_atomics[primary_token]
            else:
                add_functions[primary_token] = [["?", sub_types]]
            args = [new_token]
        # If a primary function is found, find the arguments and tokenize them
        else:
            return_args, valid_items = assign_args(primary_token, args, namespace, add_atomics, add_functions)
            if not return_args:
                return False
            return return_args[0]
    if len(args) == 1:
        return args[0]
    else:
        print("ERROR: Unspecified error, something went wrong")
        return False


def tokenize_quantifiers(tokens_tree, quantifiers):
    """
    Quantifiers are tokenized last, because they need to be written in prenex form
    to work in the prover.
    """
    # Going backwards to perserve the order of quantifiers
    place = len(quantifiers)-2
    temp = tokens_tree
    while place >= 0:
        temp = Token(quantifiers[place], [quantifiers[place+1], temp])
        place -= 2
    return temp


def tokenize_random_dcec(expression, namespace=None):
    """
    This function creates a token representation of a random DCEC statement.
    It returns the token as well as sorts of new atomics and functions.
    """
    # Default DCEC Functions
    if namespace is None:
        namespace = prototypes.Namespace()
        namespace.add_basic_dcec()
    else:
        namespace = namespace
    # Remove Comments
    temp = remove_comments(expression)
    # Check for an empty string
    if temp == "()":
        return "", {}, {}, {}
    # Check for a parentheses mismatch error
    if not cleaning.check_parens(expression):
        print("ERROR: parentheses mismatch error.")
        return False, False, False, False
    # Make symbols into functions
    temp = functorize_symbols(temp)
    # Strip comments
    temp = cleaning.strip_comments(temp)
    # Strip whitespace so you can do the rest of the parsing
    temp = cleaning.strip_white_space(temp)
    # Tuck the functions inside thier parentheses
    temp = cleaning.tuck_functions(temp)
    # Strip whitespace again
    temp = cleaning.strip_white_space(temp)
    # Consolidate Parentheses
    temp = cleaning.consolidate_parens(temp)
    quantifiers = []
    # These are the tokens that should be added to the namespace
    add_atomics = {}
    add_functions = {}
    add_quants = {}
    return_token = token_tree(temp, namespace, quantifiers, add_quants, add_atomics, add_functions)
    # check for errors that occur in the lower level
    if isinstance(return_token, bool) and return_token is False:
        return False, False, False, False
    # Add quantifiers to the TokenTree
    return_token = tokenize_quantifiers(return_token, quantifiers)
    return return_token, add_quants, add_atomics, add_functions

if __name__ == "__main__":
    import doctest
    doctest.testmod()

    # pylint: disable=invalid-name
    inputin = input("Enter an expression: ")
    # Make symbols into functions
    inputin = remove_comments(inputin)
    print(inputin)
    inputin = functorize_symbols(inputin)
    print(inputin)
    # Strip comments
    inputin = cleaning.strip_comments(inputin)
    print(inputin)
    # Strip whitespace so you can do the rest of the parsing
    inputin = cleaning.strip_white_space(inputin)
    print(inputin)
    # Tuck the functions inside thier parentheses
    inputin = cleaning.tuck_functions(inputin)
    print(inputin)
    # Consolidate Parentheses
    inputin = cleaning.consolidate_parens(inputin)
    print(inputin)
    test_namespace = prototypes.Namespace()
    test_namespace.add_basic_dcec()
    test_namespace.add_basic_numerics()
    test_namespace.add_basic_logic()
    test_namespace.add_text_function("ActionType heal Agent")
    # testNAMESPACE.addTextFunction("Boolean B Agent Moment Boolean Certainty")
    add_quant = {}
    add_atomic = {}
    add_func = {}
    tree, add_quant, add_atomic, add_func = tokenize_random_dcec(inputin, test_namespace)
    if tree is False:
        pass
    elif isinstance(tree, string_types):
        print(tree)
    else:
        tree.print_tree()
        print(tree.depth_of(), tree.width_of(), add_quant, add_atomic, add_func)
