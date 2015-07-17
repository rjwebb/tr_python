from pyparsing import Literal, Word, alphanums, ZeroOrMore, Suppress, OneOrMore, Group, Optional, lineEnd, nums, Forward, delimitedList, Regex, QuotedString
import pdb

# primitive stuff
varName = Group(Regex("[A-Z][A-Za-z_]*")("variable"))
lcName = Regex("[a-z_][A-Za-z_]*")
term = Word(alphanums + "_" )

#term = Word(alphanums + "_" )
#list_of_args = Group(term + ZeroOrMore(Suppress(",") + term))
list_of_args = Group(delimitedList(term, delim=","))

# type definition rules
integer = Group( Optional("-")("sign") + Word(nums)("num"))
#float_num = Group( Optional("-")("sign") + Regex(r'\d+(\.\d*)?([eE]\d+)?')("num") )
float_num = Group( Optional("-")("sign") + Regex(r'\d+(\.\d*)([eE]\d+)?')("num") )

#range_type = Group(Suppress("(") + integer("min") + Suppress("..") + integer("max") + Suppress(")"))
range_type = Suppress("(") + integer("min") + Suppress("..") + integer("max") + Suppress(")")
#disjunction_of_atoms = Group(term("atom") + Suppress("|") + term("atom") + ZeroOrMore(Suppress("|") + term("atom")))
disjunction_of_atoms = Group(term("atom") + Suppress("|") + delimitedList(term("atom"), delim=r"|") )

#disjunction_of_types = Group(term("type") + Suppress("||") + term("type") + ZeroOrMore(Suppress("||") + term("type")))
disjunction_of_types = Group(term("type") + Suppress("||") + delimitedList(term("type"), delim=r"||") )

type_definition = Group(term("type_def_name") + Suppress("::=") + (range_type("range") | disjunction_of_atoms("disj_atoms") | disjunction_of_types("disj_types")))

# type signature rules
single_type_declaration = Group(term("head") + Suppress(":") + Suppress("(") + list_of_args("type") + Suppress(")"))
#list_of_type_decs = single_type_declaration("type_dec") + ZeroOrMore(Suppress(",") + single_type_declaration("type_dec"))
list_of_type_decs = delimitedList(single_type_declaration("type_dec"), delim=",")
percept_type = (Literal("percept") | Literal("durative") | Literal("discrete"))
type_signature = Group(percept_type("percept_type")  + Group(list_of_type_decs)("type_decs"))

# procedure definition rules
predicate = Forward()
predicate << ( Group(lcName("head") + Optional(Suppress("(")+ Group(delimitedList(predicate))('args') + Suppress(")")))("predicate") | varName | Group(float_num("float")) | Group(integer("integer")) | Group(QuotedString("\"")("string")) )

#list_of_conditions = Group(predicate + ZeroOrMore(Suppress("&") + predicate))
list_of_conditions = Group(delimitedList(predicate, delim="&"))

#list_of_actions = Group("()" | predicate + ZeroOrMore(Suppress(",") + predicate))
list_of_actions = Group("()" | delimitedList(predicate, delim=","))

rule = Group(list_of_conditions("conditions") + Suppress("~>") + list_of_actions("actions"))("rule")
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
      type_signature_asts.append(a)
    elif "procedure_name" in a.keys():
      procedure_asts.append(a)
  
  procedure_names = [k['procedure_name'] for k in procedure_asts]
  print "procedure names:", procedure_names

  type_definitions = type_definitions_from_ast(type_definition_asts)
  type_signatures = type_signatures_from_ast(type_signature_asts)

  action_names = []
  percept_names = []

  for n in type_signatures:
    action = type_signatures[n]
    if action['percept_type'] == 'durative' or action['percept_type'] == 'discrete': # is an action
      action_names.append(n)
    elif action['percept_type'] == 'percept': # is a percept
      percept_names.append(n)
    else:
      raise Exception("unrecognised percept type?????????")
#  action_names = [name for name, action in enumerate(type_signatures) if action['percept_type'] == 'durative' or action['percept_type'] == 'discrete']

  print "actions",action_names
  print "percepts", percept_names

  procedures = {}
  for proc in procedure_asts:
    name = proc["procedure_name"]
    procedures[name] = procedure_from_ast(proc["rules"], procedure_names, action_names, percept_names)

  return { "type_definitions" : type_definitions, "type_signatures" : type_signatures, "procedures" : procedures }


def types_from_ast(ast):
  type_defs = type_definitions_from_ast(ast)
  type_sigs = type_signatures_from_ast(ast)
  return { "type_definitions" : type_defs, "type_signatures" : type_sigs }


def type_definitions_from_ast(ast):
  type_defs = []
  for item in ast:
    name = item['type_def_name']
    k = item.keys()
    if "disj_types" in k:
      e = {"name": name, "sort": "disj_types", "types": item['disj_types'].asList() }
    elif "disj_atoms" in k:
      e = {"name": name, "sort": "disj_atoms", "atoms": item['disj_atoms'].asList() }
    elif 'range' in k:
      minimum = integer_from_ast(item['range']['min'])
      maximum = integer_from_ast(item['range']['max'])
      e = {"name": name, "sort": "range", "min": minimum, "max": maximum }
    else:
      raise Exception("type definition is invalid!")
    type_defs.append(e)
  return type_defs

def integer_from_ast(ast):
  n = int(ast['num'])
  if 'sign' in ast.keys():
    if ast['sign'] == "-":
      n = -n
  return n

def type_signatures_from_ast(ast):
  sigs = {}
  for a in ast:
    for e in a['type_decs']:
#      print e['head'], "is a", a['percept_type'], "with type", e['type']
      if e['head'] in sigs:
        raise Exception("variable " + e['head'] + "'s type is defined twice!!")
      else:
        sigs[ e['head'] ] = { 'percept_type': a['percept_type'], 'type': e['type'].asList() }
  return sigs

def procedure_from_ast(ast, procedure_names, action_names, percept_names):
  return [rule_from_ast(rule, procedure_names, action_names, percept_names) for rule in ast]

def rule_from_ast(ast, procedure_names, action_names, percept_names):
  conds = [cond_from_ast(cond) for cond in ast['conditions']]

  actions = [action_from_ast(action,procedure_names,action_names) for action in ast['actions']]

  return { "conds" : conds, "actions" : actions }

def cond_from_ast(ast):
  if "head" in ast.keys(): #it is a predicate
    return predicate_from_ast(ast)
  else:
    return {"error":"not a predicate"}

def action_from_ast(ast, procedure_names, action_names):
  if ast == "()":
    return {}
  elif "head" in ast.keys(): #it is a predicate
    if ast['head'] in procedure_names: # it's a procedure call
      p = predicate_from_ast(ast)
      p['sort'] = "proc_call"
      return p
    elif ast['head'] in action_names: # it's an action
      p = predicate_from_ast(ast)
      p['sort'] = "action"
      return p
    else:
      raise Exception("the predicate " + str(ast) + " is not defined as a procedure or an action")
  else:
    raise Exception(str(ast)+" isn't a procedure call or a defined action")

def predicate_from_ast(ast):
  if "args" in ast.keys(): # it's a predicate with args
    args = [param_from_ast(p) for p in ast["args"]]
  else: # just an atom
    args = []
  return { "sort" : "predicate", "name" : ast["head"], "terms" : args }

def param_from_ast(ast):
  if type(ast) == str:
    return {"sort":"value", "value":ast, "type": "string"}
  elif "integer" in ast:
    return {"sort":"value", "value":ast["integer"], "type": "integer"}
  elif "float" in ast:
    return {"sort":"value", "value":ast["float"], "type": "float"}
  elif "string" in ast:
    return {"sort":"value", "value":ast["string"], "type": "float"}
  elif "variable" in ast:
    return {"sort":"variable", "name":ast["variable"]}
  else:
    return predicate_from_ast(ast)

def run():
    pass

if __name__ == "__main__":
    run()
