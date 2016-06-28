"""
Functions based around cleaning up expressions given in string format
"""


def tuck_functions(expression):
    """
    This function returns a string with all function calls of the form B(args)
    transformed into calls of the form (`B` args). This makes it easier to keep
    tokens on the same level.

    :param expression:
    :return:
    """
    first_paren = 0
    new_index = 0
    temp = ""
    # Find the parentheses
    while first_paren < len(expression):
        first_paren = expression.find("(", first_paren)
        if first_paren == -1:
            break
        if not(expression[first_paren-1] in [",", " ", "(", ")"]):
            func_start = first_paren-1
            while func_start >= 0:
                if expression[func_start] == "," or expression[func_start] == "(":
                    func_start += 1
                    break
                func_start -= 1
            if func_start == -1:
                func_start = 0
            funcname = expression[func_start:first_paren]
            if funcname in ["not", "negate"]:
                adder = expression[new_index:func_start] + "(" + funcname + ",("
                close_paren_place = get_matching_close_paren(expression, func_start + len(funcname))
                expression = expression[:func_start] + expression[func_start:close_paren_place] + \
                    "))" + expression[close_paren_place+1:]
                temp += adder
                new_index += len(adder)-2
            else:
                adder = expression[new_index:func_start] + "(" + funcname + ","
                temp += adder
                new_index += len(adder)-1
        first_paren += 1
    returner = temp + expression[new_index:]
    returner = returner.replace("``", "`")
    returner = returner.replace(",,", ",")
    returner = returner.replace("`", " ")
    return returner


def strip_white_space(expression):
    """
    This function strips any uneccesary whitespace from an expression. It also
    does some cleaning for different syntax. It then transforms all arguments
    seperated by whitespace or commas into arguments seperated by commas.
    Note- Commas are treated as whitespace

    :param expression:
    :return:
    """
    # Strip the whitespace around the function
    temp = expression.strip()
    # [ Have special notation, they are bracket-ish
    temp = temp.replace("[", " [")
    temp = temp.replace("]", "] ")
    # Treat commas and spaces identically
    temp = temp.replace(",", " ")
    # Strip whitespace
    while True:
        lengthpre = len(temp)
        temp = temp.replace("  ", " ")
        temp = temp.replace("( ", "(")
        temp = temp.replace(" )", ")")
        lengthpost = len(temp)
        if lengthpre == lengthpost:
            break
    # Find any touching parens, they should have a space between them
    temp = temp.replace(")(", ") (")

    # I prefer to work with commas. Makes it less confusing.
    temp = temp.replace(" ", ",")
    return temp


def strip_comments(expression):
    """
    Given an expression,
    :param expression:
    :return:
    """
    place = expression.find("#")
    if place == -1:
        return expression
    else:
        return expression[:place]


def consolidate_parens(expression):
    """
    Returns a string identical to the input except all superfluous parens are
    removed. It will also put parens around the outside of the expression, if it
    does not already have them. It will not detect a paren mismatch error.

    :param expression:
    :return:
    """
    temp = "(" + expression + ")"
    # list of indexes to delete
    delete_list = []
    # location of first paren
    first_paren_a = 0
    # looks through entire expression
    while first_paren_a < len(temp):
        # Find every occurance of a "(("
        first_paren_a = temp.find("((", first_paren_a)
        first_paren_b = first_paren_a + 1
        if first_paren_a == -1:
            break
        # Get the matching close parens.
        second_paren_a = get_matching_close_paren(temp, first_paren_a)
        second_paren_b = get_matching_close_paren(temp, first_paren_b)
        # If both the open parens and the close parens match one set of parens is uneccesary,
        # so delete them
        if second_paren_a == second_paren_b + 1:
            delete_list.append(first_paren_a)
            delete_list.append(second_paren_a)
        first_paren_a += 1
    # Make the string to return
    returner = ""
    for i in range(0, len(temp)):
        if i in delete_list:
            continue
        returner += temp[i]
    return returner


def check_parens(expression):
    """
    This function checks to see if the expression has the right number of parentheses.
    It returns true if there are an equal amount of left and right parentheses, and false if
    there are not.

    :param expression:
    :return: boolean on whether equal amount of parentheses
    """
    return expression.count("(") == expression.count(")")


def get_matching_close_paren(input_str, open_paren_index=0):
    """
    Given a string, parse through it to find the index of the closing parenthesis that matches
    the open parentheses given at some index

    :param input_str:
    :param open_paren_index:
    :return:
    """
    paren_counter = 1
    current_index = open_paren_index
    if current_index == -1:
        return False
    while paren_counter > 0:
        close_index = input_str.find(")", current_index + 1)
        open_index = input_str.find("(", current_index + 1)
        if (open_index < close_index or close_index == -1) and open_index != -1:
            current_index = open_index
            paren_counter += 1
        elif(close_index < open_index or open_index == -1) and close_index != -1:
            current_index = close_index
            paren_counter -= 1
        else:
            return False
    return current_index
