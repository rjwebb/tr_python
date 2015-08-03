import copy

# BUILT IN DEFINITIONS OF ACTIONS
built_in_signatures = {
  "remember" : {"percept_type" : "special_action", "type" : "predicate"},
  "forget" : {"percept_type" : "special_action", "type" : "predicate"}
}


def program_from_ast(ast):
  """
  Convert the result of parsing a TR program into the representation used by the interpreter

  """

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
    ptype = action['percept_type']
    if ptype == 'durative' or \
       ptype == 'discrete' or \
       ptype == 'special_action': # is an action
      action_names.append(n)
    elif ptype == 'percept': # is a percept
      percept_names.append(n)
    else:
      raise Exception("unrecognised percept type for " + str(n))


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
    raise Exception("the type signature and the definition for " + name + \
                    " have different numbers of terms! (" + str(input_types) + 
                    ", " + str(parameters) + ")")
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
