from pyparsing import Literal, Word, alphanums, ZeroOrMore, Suppress, OneOrMore, Group, Optional, lineEnd, nums, Forward, delimitedList, Regex, QuotedString, infixNotation, opAssoc, oneOf

# basic syntax things
varName = Group(Regex("[A-Z][A-Za-z0-9_]*")("variable"))
lcName = Regex("[a-z_][A-Za-z0-9_]*")
term = Word(alphanums + "_" )

list_of_args = Group(delimitedList(lcName, delim=","))

# primitive types
integer = Group( Optional("-")("sign") + Word(nums)("num"))
float_num = Group( Optional("-")("sign") + Regex(r'\d+(\.\d*)([eE]\d+)?')("num") )

# rules for parsing expressions
binary_comparison = Literal(">=") | Literal(">") | Literal("==") | Literal("<=") | Literal("<")

simple_expression = varName | Group(float_num("float")) | Group(integer("integer"))
expression = infixNotation(simple_expression,
                           [
                             (oneOf("* /"), 2, opAssoc.LEFT),
                             (oneOf("+ -"), 2, opAssoc.LEFT)
                           ])

# type definition rules
range_type = Suppress("(") + integer("min") + Suppress("..") + integer("max") + Suppress(")")
disjunction_of_atoms = Group(lcName("atom") + Suppress("|") + delimitedList(lcName("atom"), delim=r"|") )
disjunction_of_types = Group(lcName("type") + Suppress("||") + delimitedList(lcName("type"), delim=r"||") )

type_definition = Group(lcName("type_def_name") + Suppress("::=") + (range_type("range") | disjunction_of_atoms("disj_atoms") | disjunction_of_types("disj_types")))

# type signature rules
single_type_declaration = Group(lcName("head") + Suppress(":") + Suppress("(") + Optional(list_of_args("type")) + Suppress(")"))
list_of_type_decs = delimitedList(single_type_declaration("type_dec"), delim=",")

percept_type = (Literal("percept") | Literal("durative") | Literal("discrete"))
type_signature = Group(percept_type("percept_type")  + Group(list_of_type_decs)("type_decs"))

# procedure definition rules
predicate = Forward()
predicate << ( Group(lcName("head") + Optional(Suppress("(")+ Group(delimitedList(predicate))('args') + Suppress(")")))("predicate") | varName | Group(float_num("float")) | Group(integer("integer")) | Group(QuotedString("\"")("string")) )

binary_condition = Group(expression("arg1") + binary_comparison("operator") + expression("arg2"))

list_of_conditions = Group(delimitedList(( binary_condition | Group(Literal("not") + predicate("negation")) | predicate ), delim="&"))
list_of_actions = Group("()" | delimitedList(predicate, delim=","))

rule = Group(list_of_conditions("conditions") + Suppress("~>") + list_of_actions("actions"))("rule")
rules = Group(OneOrMore(rule))

procedure_params = Suppress("(") + Group(delimitedList(varName))("parameters") + Suppress(")")
procedure = Group(lcName("procedure_name") + Optional( procedure_params ) + Suppress("{") + rules("rules") + Suppress("}"))

procedure_type_signature = Group(lcName("procedure_name") + Suppress(":") + Suppress("(") + Optional(Group(delimitedList(lcName))("type")) + Suppress(")") + Suppress("~>") )

program_item = type_definition("type_definition") | type_signature("type_signature") | procedure("procedure") | procedure_type_signature("procedure_type_signature")

program = OneOrMore(program_item)("program")

