from pyparsing import Word, alphanums, ZeroOrMore, Suppress, OneOrMore, Group, Optional, lineEnd, nums

# primitive stuff
term = Word(alphanums + "_" )
list_of_args = Group(term + ZeroOrMore(Suppress(",") + term))


# type definition rules
range_type = Suppress("(") + Optional("-") + Word(nums) + Suppress(")")
disjunction_of_atoms = term + ZeroOrMore(Suppress("|") + term)

disjunction_of_types = term + ZeroOrMore(Suppress("|") + term)

type_definition = term("head") + Suppress("::=") + Group(range_type("range") | disjunction_of_atoms("disj_atoms") | disjunction_of_types("disj_types"))

single_type_declaration = term("head") + Suppress(":") + Suppress("(") + list_of_args("type") + Suppress(")")

type_declaration = ("percept" | "durative" | "discrete") + single_type_declaration + ZeroOrMore(Suppress(",") + single_type_declaration)

# procedure definition rules
predicate = Group(term("head") + Optional(Suppress("(")+ list_of_args("args") + Suppress(")")))
list_of_predicates = Group(predicate + ZeroOrMore(Suppress("&") + predicate))

list_of_actions = Group("()" | predicate + ZeroOrMore(Suppress(",") + predicate))

rule = Group(list_of_predicates("conditions") + Suppress("~>") + list_of_actions("actions"))("rule")
rules = Group(ZeroOrMore(rule))
procedure = Group(term("name") + Suppress("{") + rules("rules") + Suppress("}"))

program = Group(OneOrMore(procedure))("procedures")

def run():
    test_proc = """get_object{
holding & see(0,centre) ~> ()
holding & see(0,centre) ~> grab(100)
holding ~> get_to
true ~> release(1)
}"""

    test_program = """get_object{
holding & see(0,centre) ~> ()
holding & see(0,centre) ~> grab(100)
holding ~> get_to
true ~> release(1)
}

get_to {
see(0, centre)    ~> ()
see(0, Dir)       ~> turn(Dir)
see(_, centre)    ~> move(6)
see(_, Dir)       ~> move(4) , turn(Dir)
true              ~> turn(left)
}

"""


if __name__ == "__main__":
    run()
