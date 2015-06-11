from pyparsing import Word, alphanums, ZeroOrMore, Suppress, OneOrMore, Group, Optional, lineEnd

term = Word(alphanums + "_" )
list_of_args = Group(term + ZeroOrMore(Suppress(",") + term))

predicate = Group(term("head") + Optional(Suppress("(")+ list_of_args("args") + Suppress(")")))
list_of_predicates = Group(predicate + ZeroOrMore(Suppress("&") + predicate))

list_of_actions = "()" | Group(predicate + ZeroOrMore(Suppress(",") + predicate))

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
