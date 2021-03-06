from pyparsing import Literal, Word, alphanums, ZeroOrMore, Suppress, OneOrMore, Group, Optional, lineEnd, nums, Forward, delimitedList, Regex, QuotedString, infixNotation, opAssoc, oneOf

"""
Parsing rules for the teleo-reactive language

This uses pyparsing, a parser library for Python
"""


"""
parsing variable names, terms, atoms
"""
varName = Regex("[A-Z][A-Za-z0-9_]*")
lcName = Regex("[a-z_][A-Za-z0-9_]*")
term = Word(alphanums + "_" )


"""
primitive type definitions
"""
integer = Group( Optional("-")("sign") + Word(nums)("num"))
float_num = Group( Optional("-")("sign") + Regex(r'\d+(\.\d*)([eE]\d+)?')("num") )
string_value = QuotedString("\"")


"""
rules to parse type definitions
e.g. 

disjunction of atoms:
object ::= book | hat | car
person ::= bob | jane | emma

disjunction of types:
thing ::= object || person

range (of integers):
age ::= (0 .. 120)
"""
range_type = Suppress("(") + integer("min") + Suppress("..") + integer("max") + Suppress(")")
disjunction_of_atoms = Group(lcName("atom") + Suppress("|") + delimitedList(lcName("atom"), delim=r"|") )
disjunction_of_types = Group(lcName("type") + Suppress("||") + delimitedList(lcName("type"), delim=r"||") )

type_definition = Group(lcName("type_def_name") + Suppress("::=") + (range_type("range") | disjunction_of_atoms("disj_atoms") | disjunction_of_types("disj_types")))


"""
rules to parse type declarations
e.g.

percept thing : (),
        see   : (object, num, num)
"""
single_type_declaration = Group(lcName("head") + Suppress(":") + Suppress("(") + Optional(Group(delimitedList(lcName))("type")) + Suppress(")"))
list_of_type_decs = delimitedList(single_type_declaration("type_dec"))

percept_type = Literal("percept") | \
               Literal("durative") | \
               Literal("discrete") | \
               Literal("belief")
type_signature = Group(percept_type("percept_type")  + Group(list_of_type_decs)("type_decs"))


"""
a predicate is defined recursively, hence the Forward() rule
"""
predicate = Forward()
predicate << (~Literal("not") + Group(lcName("head") + Optional(Suppress("(")+ Group(delimitedList(predicate))('args') + Suppress(")")))("predicate") | Group(varName("variable")) | Group(float_num("float")) | Group(integer("integer")) | Group(string_value("string")) )


"""
the RHS of the rule is a list of actions, or no action "()"
"""
list_of_actions = Group("()" | delimitedList(predicate, delim=","))


"""
rules for parsing expressions
i.e. something that is evaluated to a value, like "2 + 1" or "1 / 6"
"""
simple_expression = Group(varName("variable")) | Group(float_num("float")) | Group(integer("integer"))
expression = infixNotation(simple_expression,
                           [
                             (oneOf("* /"), 2, opAssoc.LEFT),
                             (oneOf("+ -"), 2, opAssoc.LEFT)
                           ])


"""
binary comparison symbols
"""
binary_comparison = Literal(">=") | Literal(">") | Literal("==") | Literal("<=") | Literal("<")


"""
rule for parsing binary conditions, like
"2 > 1" or "X <= 5 + Y"
"""
binary_condition = Group(expression("arg1") + binary_comparison("operator") + expression("arg2"))


"""
the LHS of the rule is a list of conditions, which are either predicates, negated predicates or binary comparison conditions
"""

condition = binary_condition("binary_condition") | predicate
list_of_conditions = infixNotation(condition,
                                   [
                                       (Literal("not")("negation"), 1, opAssoc.RIGHT),
                                       (Literal("&")("conjunction"), 2, opAssoc.LEFT)
                                   ])

"""
a single TR rule,
e.g.
see(thing, 10) ~> move_forward
"""
while_cond = Suppress("while") + list_of_conditions("while_conditions") + Optional(Suppress("min") + float_num("while_minimum"))
until_cond = Suppress("until") + list_of_conditions("until_conditions") + Optional(Suppress("min") + float_num("until_minimum"))
ruleLHS = list_of_conditions("guard_conditions") + Optional(while_cond) + Optional(until_cond)
rule = Group(ruleLHS + Suppress("~>") + list_of_actions("actions"))("rule")
rules = Group(OneOrMore(rule))


"""
procedure definition
"""
procedure_params = Suppress("(") + Optional(delimitedList(Group(varName("variable")))) + Suppress(")")
procedure = Group(lcName("procedure_name") + procedure_params("parameters") + Suppress("{") + rules("rules") + Suppress("}"))


"""
the procedure type signature
"""
procedure_type_signature = Group(lcName("procedure_name") + Suppress(":") + Suppress("(") + Optional(Group(delimitedList(lcName))("type")) + Suppress(")") + Suppress("~>") )


"""
rule for a program item
"""
program_item = type_definition("type_definition") | \
               type_signature("type_signature") | \
               procedure("procedure") | \
               procedure_type_signature("procedure_type_signature")


"""
rule for a complete program
"""
program = OneOrMore(program_item)("program")

