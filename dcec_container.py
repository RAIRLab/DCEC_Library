from __future__ import print_function
import pickle
from six import string_types
from six.moves import input

# We need to use the first type of import if running this script directly and the second type of
# import if we're using it in a package (such as for within Talos)
try:
    import high_level_parsing
    import prototypes
except ImportError:
    import DCEC_Library.high_level_parsing as high_level_parsing
    import DCEC_Library.prototypes as prototypes


class DCECContainer:
    def __init__(self):
        self.namespace = prototypes.Namespace()
        self.statements = []
        self.checkMap = {}

    def save(self, filename):
        """
        Saves a given container to file, saving both the prototypes (namespace) within the
        container as well as the statements that have been added to it.

        :param filename:
        :return:
        """
        namespace_out = open(filename + ".namespace", "w")
        statements_out = open(filename + ".statements", "w")
        pickle.dump(self.namespace, namespace_out)
        pickle.dump(self.checkMap, statements_out)

    def load(self, filename):
        name_in = open(filename + ".namespace", "r")
        state_in = open(filename + ".statements", "r")
        namespace_in = pickle.load(name_in)
        statements_in = pickle.load(state_in)
        if isinstance(namespace_in, prototypes.Namespace):
            self.namespace = statements_in
        else:
            return False
        if isinstance(statements_in, dict):
            self.statements = statements_in.keys()
            self.checkMap = statements_in

    def print_statement(self, statement, expression_type="S"):
        if isinstance(statement, string_types):
            return statement
        if expression_type == "S":
            temp = statement.create_s_expression()
        elif expression_type == "F":
            temp = statement.create_f_expression()
        else:
            print("ERROR: invalid notation type")
            return False
        for quant in self.namespace.quant_map.keys():
            if 'QUANT' in quant:
                temp = temp.replace(quant, self.namespace.quant_map[quant])
        return temp

    def add_statement(self, statement):
        """
        Given a statement, attempts to parse the statement into the DCEC*. If there's an issue,
        it'll print the issue and then return False, otherwise it'll return True and add the
        statement to the Container instance
        :param statement:
        :return:
        """
        add_atomics = {}
        add_functions = {}
        add_quants = {}
        addee = statement
        if isinstance(addee, string_types):
            addee, add_quants, \
             add_atomics, add_functions = high_level_parsing.tokenize_random_dcec(addee,
                                                                                  self.namespace)
            if isinstance(addee, bool) and not addee:
                print("ERROR: the statement " + str(statement) + " was not correctly formed.")
                return False
            elif addee == "":
                return True
        elif isinstance(addee, high_level_parsing.Token):
            pass
        else:
            print("ERROR: the input " + str(statement) + " was not of the correct type.")
            return False
        for atomic in add_atomics.keys():
            # Tokens are not currently stored
            if isinstance(atomic, high_level_parsing.Token):
                continue
            for potentialtype in range(0, len(add_atomics[atomic])):
                if (not self.namespace.no_conflict(add_atomics[atomic][0],
                                                   add_atomics[atomic][potentialtype], 0)[0]) and \
                        (not self.namespace.no_conflict(add_atomics[atomic][potentialtype],
                                                        add_atomics[atomic][0], 0)[0]):
                    print("ERROR: The atomic " + atomic + " cannot be both " +
                          add_atomics[atomic][potentialtype] + " and " + add_atomics[atomic][0] +
                          ". (This is caused by assigning different sorts to two atomics inline. "
                          "Did you rely on the parser for sorting?)")
                    return False
        for function in add_functions.keys():
            for item in add_functions[function]:
                if item[0] == "?":
                    print("ERROR: please define the returntype of the inline function " + function)
                    return False
                else:
                    self.namespace.add_code_function(function, item[0], item[1])
        for atomic in add_atomics.keys():
            # Tokens are not currently stored
            if isinstance(atomic, high_level_parsing.Token):
                continue
            elif atomic in self.namespace.atomics.keys():
                if not self.namespace.no_conflict(self.namespace.atomics[atomic],
                                                  add_atomics[atomic][0], 0)[0] and \
                        not self.namespace.no_conflict(add_atomics[atomic][0],
                                                       self.namespace.atomics[atomic], 0)[0]:
                    print("ERROR: The atomic "+atomic+" cannot be both " + add_atomics[atomic][0] +
                          " and " + self.namespace.atomics[atomic] + ".")
                    return False
            else:
                self.namespace.add_code_atomic(atomic, add_atomics[atomic][0])
        for quant in add_quants.keys():
            if 'QUANT' in quant:
                self.namespace.quant_map[quant] = add_quants[quant]
        self.statements.append(addee)
        if not isinstance(addee, string_types):
            self.checkMap[addee.create_s_expression()] = addee
        else:
            self.checkMap[addee] = addee
        return True

    def sort_of(self, statement):
        if isinstance(statement, string_types):
            return self.namespace.atomics.get(statement)
        if statement is None:
            return None
        if statement.function_name not in self.namespace.functions.keys():
            return None
        tmp_func = statement.function_name
        tmp_args = statement.args
        tmp_types = []
        for arg in tmp_args:
            tmp_types.append(self.sort_of(arg))
        for x in self.namespace.functions[tmp_func]:
            if len(x[1]) != len(tmp_types):
                continue
            else:
                returner = True
                for r in range(0, len(x[1])):
                    if not tmp_types[r] is None and self.namespace.no_conflict(tmp_types[r], x[1][r], 0)[0]:
                        continue
                    else:
                        returner = False
                        break
                if returner:
                    return x[0]
                else:
                    continue
        return None

    def sorts_of_params(self, statement):
        sorts = []
        if isinstance(statement, string_types):
            return sorts
        if statement is None:
            return None
        if statement.function_name not in self.namespace.functions.keys():
            return None
        tmp_func = statement.function_name
        tmp_args = statement.args
        tmp_types = []
        for arg in tmp_args:
            tmp_types.append(self.sort_of(arg))
        for x in self.namespace.functions[tmp_func]:
            if len(x[1]) != len(tmp_types):
                continue
            else:
                returner = True
                for r in range(0, len(x[1])):
                    if not tmp_types[r] is None and \
                            self.namespace.no_conflict(tmp_types[r], x[1][r], 0)[0]:
                        continue
                    else:
                        returner = False
                        break
                if returner:
                    return x[1]
                else:
                    continue
        return None

    def stupid_sort_define(self, sort, old_container):
        if sort in self.namespace.sorts.keys():
            return
        else:
            for x in old_container.namespace.sorts[sort]:
                self.stupid_sort_define(x, old_container)
            self.namespace.add_code_sort(sort, old_container.namespace.sorts[sort])

    # TODO replace with iterator
    def stupid_loop(self, token, functions, atomics, old_container):
        if isinstance(token, string_types):
            if old_container.sort_of(token) is None:
                self.stupid_sort_define(atomics[token][0], old_container)
                self.namespace.add_code_atomic(token, atomics[token][0])
            else:
                self.stupid_sort_define(old_container.sort_of(token), old_container)
                self.namespace.add_code_atomic(token, old_container.sort_of(token))
        else:
            if token.function_name in ["forAll", "exists"]:
                pass
            elif old_container.sort_of(token) is None:
                arg_types = []
                for arg in token.args:
                    arg_types.append(atomics[arg][0])
                if token in atomics.keys():
                    self.stupid_sort_define(atomics[token][0], old_container)
                    for arg in arg_types:
                        self.stupid_sort_define(arg, old_container)
                    poss = []
                    mapping = {}
                    for func in old_container.namespace.functions[token.function_name]:
                        deep = 0
                        compat, depth = old_container.namespace.no_conflict(func[0],
                                                                            atomics[token][0], 0)
                        if not compat:
                            continue
                        else:
                            deep += depth
                        args = [atomics[arg][0] for arg in token.args]
                        if len(args) != len(func[1]):
                            continue
                        for y in range(0, len(func[1])):
                            compat, depth = old_container.namespace.no_conflict(args[y],
                                                                                func[1][y], 0)
                            deep += depth
                        poss.append(deep)
                        mapping[deep] = func
                    final = mapping[min(poss)]
                    self.namespace.add_code_function(token.function_name, final[0], final[1])
                else:
                    # This should never happen, but if it does make a new function
                    for x in functions[token.function_name]:
                        self.stupid_sort_define(x[0], old_container)
                        for y in x[1]:
                            self.stupid_sort_define(y, old_container)
                        self.namespace.add_code_function(token.function_name, x[0], x[1])
            else:
                self.stupid_sort_define(old_container.sort_of(token), old_container)
                for x in old_container.sorts_of_params(token):
                    self.stupid_sort_define(x, old_container)
                self.namespace.add_code_function(token.function_name, old_container.sort_of(token),
                                                 old_container.sorts_of_params(token))
            for arg in token.args:
                self.stupid_loop(arg, functions, atomics, old_container)

    def tokenize(self, statement):
        if not isinstance(statement, string_types):
            return False
        dcec_container = DCECContainer()
        stuff = high_level_parsing.tokenize_random_dcec(statement, self.namespace)
        if isinstance(stuff[0], bool) and not stuff[0]:
            return False
        elif stuff[0] == "":
            return True
        dcec_container.stupid_loop(stuff[0], stuff[3], stuff[2], self)
        dcec_container.add_statement(statement)
        return dcec_container

if __name__ == "__main__":
    test = DCECContainer()
    test.namespace.add_basic_dcec()
    test.namespace.add_basic_logic()
    test.namespace.add_text_function("Boolean help Object")
    test.namespace.add_text_function("Boolean kind Agent")
    test.namespace.add_text_function("Agent james")
    #test.namespace.addTextFunction("Agent james")
    #test.namespace.addTextFunction("Boolean hello Object")
    #test.namespace.addTextFunction("Boolean equals Object Object")
    #test.namespace.addTextAtomic("Boolean earth")
    #test.namespace.addTextSort(raw_input("Enter a sort: "))
    #test.namespace.addTextSort(raw_input("Enter a sort: "))
    #test.namespace.addTextSort(raw_input("Enter a sort: "))
    #test.tokenize(raw_input("Enter an expression: "))
    test.add_statement(input("Enter an expression: "))
    new = test.tokenize(input("Enter an expression: "))
    #print new.statements[0].createSExpression(),new.namespace.atomics
    #test.save("TEST")
    print(test.statements, test.namespace.atomics, test.namespace.functions)
    print(new.statements, new.namespace.atomics, new.namespace.functions)
    #new.load("TEST")
    #print len(test.statements)
    for x in test.statements:
        #print test.printStatement(x)
        pass
    #print test.namespace.atomics
    #print test.namespace.functions
    #print test.namespace.sorts
    if len(test.statements) > 0:
        #print test.sortsOfParams(test.statements[0])
        #print test.sortOf(test.statements[0])
        pass