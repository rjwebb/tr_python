from pyparsing import Literal, Word, alphanums, ZeroOrMore, Suppress, OneOrMore, Group, Optional, lineEnd, nums

# primitive stuff
term = Word(alphanums + "_" )
list_of_args = Group(term + ZeroOrMore(Suppress(",") + term))

# type definition rules
integer = Group( Optional("-")("sign") + Word(nums)("num"))

range_type = Group(Suppress("(") + integer("min") + Suppress("..") + integer("max") + Suppress(")"))
disjunction_of_atoms = Group(term("atom") + Suppress("|") + term("atom") + ZeroOrMore(Suppress("|") + term("atom")))
disjunction_of_types = Group(term("type") + Suppress("||") + term("type") + ZeroOrMore(Suppress("||") + term("type")))

type_definition = Group(term("type_def_name") + Suppress("::=") + (range_type("range") | disjunction_of_types("disj_types") | disjunction_of_atoms("disj_atoms")))


# type signature rules
single_type_declaration = Group(term("head") + Suppress(":") + Suppress("(") + list_of_args("type") + Suppress(")"))
list_of_type_decs = single_type_declaration("type_dec") + ZeroOrMore(Suppress(",") + single_type_declaration("type_dec"))
percept_type = (Literal("percept") | Literal("durative") | Literal("discrete"))
type_signature = Group(percept_type("percept_type")  + Group(list_of_type_decs)("type_decs"))

# procedure definition rules
predicate = Group(term("head") + Optional(Suppress("(")+ list_of_args("args") + Suppress(")")))("predicate")
list_of_predicates = Group(predicate + ZeroOrMore(Suppress("&") + predicate))

list_of_actions = Group("()" | predicate + ZeroOrMore(Suppress(",") + predicate))

rule = Group(list_of_predicates("conditions") + Suppress("~>") + list_of_actions("actions"))("rule")
rules = Group(OneOrMore(rule))
procedure = Group(term("procedure_name") + Suppress("{") + rules("rules") + Suppress("}"))

program_item = type_definition("type_definition") | type_signature("type_signature") | procedure("procedure")

program = OneOrMore(program_item)("program")

def program_from_ast(ast):
  type_definition_asts = []
  type_signature_asts = []
  procedure_asts = []

  for a in ast:
    if "type_def_name" in a.keys():
      type_definition_asts.append(a)
    elif "percept_type" in a.keys():
      type_definition_asts.append(a)
    elif "procedure_name" in a.keys():
      procedure_asts.append(a)
  
  print "type defs:",[k.asList() for k in type_definition_asts]
  print "type sigs:",[k.asList() for k in type_signature_asts]
  print "procs:",[k.asList() for k in procedure_asts]

def sfsdjfkds():
  types = types_from_ast(ast['type_info'])

  procedures = {}
  for proc in ast["procedures"]:
    name = proc["name"]
    procedures[name] = procedure_from_ast(proc["rules"])

  return { "types" : types, "procedures" : procedures }


def types_from_ast(ast):
  type_defs = type_definitions_from_ast(ast)
  type_sigs = type_signatures_from_ast(ast)
  return { "type_definitions" : type_defs, "type_signatures" : type_sigs }


def type_definitions_from_ast(ast):

  return {}

def type_signatures_from_ast(ast):
  sigs = {}
  for a in ast:
    for e in a['type_decs']:
      print e['head'], "is a", a['percept_type'], "with type", e['type']
      if e['head'] in sigs:
        raise Exception("variable " + e['head'] + "'s type is defined twice!!")
      else:
        sigs[ e['head'] ] = { 'percept_type': a['percept_type'], 'type': e['type'].asList() }
  return sigs

def procedure_from_ast(ast):
  return [rule_from_ast(rule) for rule in ast]

def rule_from_ast(ast):
  conds = [cond_from_ast(cond) for cond in ast['conditions']]
  actions = [action_from_ast(action) for action in ast['actions']]

  return { "conds" : conds, "actions" : actions }

def cond_from_ast(ast):
  if "head" in ast.keys(): #it is a predicate
    return predicate_from_ast(ast)
  else:
    return {"error":"not a predicate"}

def action_from_ast(ast):
  if ast == "()":
    return {}
  elif "head" in ast.keys(): #it is a predicate
    return predicate_from_ast(ast)
  else:
    return {"error":"not a predicate"}

def predicate_from_ast(ast):
  if "args" in ast.keys(): # if has args
    args = [param_from_ast(p) for p in ast["args"]]
  else:
    args = []
  return { "sort" : "predicate", "name" : ast["head"], "terms" : args }

def param_from_ast(ast):
  if type(ast) == str:
    return {"sort":"value", "value":ast}
  else:
    return predicate_from_ast(ast)

def run():
    pass
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

test_program2 = """durative facing_direction : (num)
top_task{
    true ~> turn_left
}"""

test_program3 = """arm ::= arm1 | arm2
table ::= table1 | shared | table2
block ::= (1 .. 16)
place ::= table || block

percept
  holding : (arm, block),
  on : (block, place)

durative
  move : (num)

get_object{
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

test_typedef = """arm ::= arm1 | arm2
table ::= table1 | shared | table2
block ::= (1 .. 16)
place ::= table || block
"""

test_typesig = """percept
  holding : (arm, block),
  on : (block, place)

durative
  move : (num)
"""


if __name__ == "__main__":
    run()
