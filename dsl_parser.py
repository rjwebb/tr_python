from pyparsing import Literal, Word, alphanums, ZeroOrMore, Suppress, OneOrMore, Group, Optional, lineEnd, nums, Forward, delimitedList, Regex, QuotedString, infixNotation, opAssoc, oneOf
import pdb
import copy

# basic syntax things
varName = Group(Regex("[A-Z][A-Za-z0-9_]*")("variable"))
lcName = Regex("[a-z_][A-Za-z_]*")
term = Word(alphanums + "_" )

list_of_args = Group(delimitedList(term, delim=","))

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
disjunction_of_atoms = Group(term("atom") + Suppress("|") + delimitedList(term("atom"), delim=r"|") )
disjunction_of_types = Group(term("type") + Suppress("||") + delimitedList(term("type"), delim=r"||") )

type_definition = Group(term("type_def_name") + Suppress("::=") + (range_type("range") | disjunction_of_atoms("disj_atoms") | disjunction_of_types("disj_types")))

# type signature rules
single_type_declaration = Group(term("head") + Suppress(":") + Suppress("(") + Optional(list_of_args("type")) + Suppress(")"))
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
procedure = Group(term("procedure_name") + Optional( procedure_params ) + Suppress("{") + rules("rules") + Suppress("}"))

procedure_type_signature = Group(term("procedure_name") + Suppress(":") + Suppress("(") + Optional(Group(delimitedList(term))("type")) + Suppress(")") + Suppress("~>") )

program_item = type_definition("type_definition") | type_signature("type_signature") | procedure("procedure") | procedure_type_signature("procedure_type_signature")

program = OneOrMore(program_item)("program")


# BUILT IN DEFINITIONS OF ACTIONS
built_in_signatures = {
  "remember" : {"percept_type" : "special_action", "type" : "predicate"},
  "forget" : {"percept_type" : "special_action", "type" : "predicate"}
}


def program_from_ast(ast):
  type_definition_asts = []
  type_signature_asts = []
  procedure_asts = []
  procedure_sig_asts = []

  for a in ast:
    if "type_def_name" in a.keys():
      type_definition_asts.append(a)
    elif "percept_type" in a.keys():
      type_signature_asts.append(a)
    elif "rules" in a.keys():
      procedure_asts.append(a)
    elif "procedure_name" in a.keys():
      procedure_sig_asts.append(a)

  procedure_names = [k['procedure_name'] for k in procedure_asts]
  #print "procedure names:", procedure_names

  type_definitions = type_definitions_from_ast(type_definition_asts)

  parsed_type_signatures = type_signatures_from_ast(type_signature_asts)
  type_signatures = {}
  
  for k,v in parsed_type_signatures.items():
    if k in type_signatures:
      raise Exception("duplicate type signature for " + k + " "  + str(v))
    else:
      type_signatures[k] = v

  for k,v in built_in_signatures.items():
    if k in type_signatures:
      raise Exception(k + " is a reserved built-in predicate name!")
    else:
      type_signatures[k] = v

  procedure_signatures = procedure_signatures_from_ast(procedure_sig_asts)

  action_names = []
  percept_names = []

  for n in type_signatures:
    action = type_signatures[n]
    if action['percept_type'] == 'durative' or \
       action['percept_type'] == 'discrete' or \
       action['percept_type'] == 'special_action': # is an action
      action_names.append(n)
    elif action['percept_type'] == 'percept': # is a percept
      percept_names.append(n)
    else:
      raise Exception("unrecognised percept type for " + str(n))


  print "actions:",action_names
  print "percepts:", percept_names

  procedures = {}
  for proc in procedure_asts:
    name = proc["procedure_name"]
    procedure_signature = procedure_signatures[name]
    procedures[name] = procedure_from_ast(proc, procedure_signature, procedure_names, action_names, percept_names)
  return { "type_definitions" : type_definitions,
           "type_signatures" : type_signatures,
           "procedures" : procedures}

def procedure_parameters_from_ast(ast):
  output = []
  for a in ast:
    paramName = str(a["variable"])
    output.append( { "name" : paramName, "sort" : "variable" } )
  return output

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

def float_from_ast(ast):
  n = float(ast['num'])
  if 'sign' in ast.keys():
    if ast['sign'] == "-":
      n = -n
  return n


def type_signatures_from_ast(ast):
  sigs = {}
  for a in ast:
    for e in a['type_decs']:
      if e['head'] in sigs:
        raise Exception("variable " + e['head'] + "'s type is defined twice!!")
      else:
        if 'type' in e:
          # the percept is a predicate
          t = e['type'].asList()
        else:
          # the percept is an atom
          t = []
        sigs[ e['head'] ] = { 'percept_type': a['percept_type'], 'type': t}
  return sigs

def procedure_from_ast(procedure_ast, input_types, procedure_names, action_names, percept_names):
  name = procedure_ast["procedure_name"]

  rules = []
  for rule in procedure_ast["rules"]:
    r = rule_from_ast(rule, procedure_names, action_names, percept_names)
    rules.append(r)

  try:
    parameters = procedure_parameters_from_ast(procedure_ast["parameters"])
  except KeyError:
    parameters = []

  if len(input_types) != len(parameters):
    print input_types, parameters
    raise Exception("the type signature and the definition for " + name + " have different numbers of terms!")
  else:
    parameters_with_types = []
    for p, t in zip(parameters, input_types):
      p_t = copy.copy(p)
      p_t["type"] = t
      parameters_with_types.append(p_t)

    return {"name" : name,
            "rules" : rules,
            "parameters" : parameters_with_types}

def rule_from_ast(ast, procedure_names, action_names, percept_names):
  conds = [cond_from_ast(cond) for cond in ast['conditions']]
  if ast['actions'][0] == "()":
    actions = []
  else:
    actions = [action_from_ast(action,procedure_names,action_names) for action in ast['actions']]
  return { "conds" : conds, "actions" : actions }

def cond_from_ast(ast):
  if "negation" in ast.keys():
    # it's a negation of a predicate
    inner_predicate = cond_from_ast(ast['negation'])
    return {"sort" : "negation", "predicate" : inner_predicate}
  if "head" in ast.keys(): #it is a predicate
    return predicate_from_ast(ast)
  elif "operator" in ast:
    arg1 = expression_from_ast(ast["arg1"])
    arg2 = expression_from_ast(ast["arg2"])
    return {"sort":"binary_condition", "operator":ast["operator"], "arg1":arg1, "arg2":arg2}
  else:
    raise Exception(str(ast) + " is not a predicate, negation or binary comparison!")

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

def expression_from_ast(ast):
  if len(ast) == 1:
    return param_from_ast(ast)
  else:
    left = expression_from_ast(ast[0])
    operator = ast[1]
    right = expression_from_ast(ast[2])
    return {"sort" : "binary_operation", "operator" : operator, "left" : left, "right" : right }

def param_from_ast(ast):
  if type(ast) == str:
    return {"sort":"value", "value":ast, "type": "atom"}
  elif "integer" in ast:
    return {"sort":"value", "value":integer_from_ast(ast["integer"]), "type": "integer"}
  elif "float" in ast:
    return {"sort":"value", "value":float_from_ast(ast["float"]), "type": "float"}
  elif "string" in ast:
    return {"sort":"value", "value":ast["string"], "type": "float"}
  elif "variable" in ast:
    return {"sort":"variable", "name":ast["variable"]}
  else:
    return predicate_from_ast(ast)

def procedure_signatures_from_ast(ast):
  output = {}
  for a in ast:
    name = a["procedure_name"]
    if name not in output:

      if "type" in a:
        proc_type = a["type"].asList()
      else:
        proc_type = []
      output[name] = proc_type

    else:
      raise Exception(name + " has a duplicate type signature!")

  return output

def run():
    pass

if __name__ == "__main__":
    run()
