import copy

# BUILT IN DEFINITIONS OF ACTIONS
built_in_signatures = {
  "remember" : {"percept_type" : "special_action", "type" : ["predicate"], "sort" : "action"},
  "forget" : {"percept_type" : "special_action", "type" : ["predicate"], "sort" : "action"}
}

NOT_TRUE = {"sort" : "negation",
            "predicate" : {"sort" : "predicate",
                           "name" : "true",
                           "terms" : []
                         }
          }


def type_check(arg, expected_type, type_definitions, parameters):
  """
  Check that a given thing "arg" is of a given type "expected_type"
  type_definitions consists of the definitions for user-defined types
  parameters is the variable instantiations
  """
  # primitive types
  if expected_type == 'string':
    return (arg['sort'] == 'value' and arg['type'] == 'string') or arg['sort'] == 'variable'

  elif expected_type == 'num':
    is_val = arg['sort'] == 'value'
    is_var = arg['sort'] == 'variable'
    return (is_val and (arg['type'] == 'integer' or arg['type'] == 'float')) or is_var

  # user defined type
  else:
    if arg['sort'] == 'predicate':
      expected_type_definition = type_definitions[expected_type]
      s = expected_type_definition['sort']

      # disjunction of atoms type
      if s == "disj_atoms":
        atoms = expected_type_definition['atoms']
        return arg['name'] in atoms

      # disjunction of types type
      elif s == "disj_types":
        types = expected_type_definition['types']
        for t in types:
          if type_check(arg, t, type_definitions, parameters):
            return True
        return False

      # range type
      elif s == "range_type":
        is_num = type_check(arg, "num", type_definitions, parameters)
        if is_num:
          max_val = expected_type_definition['max']
          min_val = expected_type_definition['min']
          val = arg['value']
          return val >= min_val and val <= max_val
        else:
          return False
      else:
        raise Exception("Invalid type definition "+ str(expected_type_definition))
    else:
      return False



def type_check_args(args, expected_types, type_definitions, parameters):
  """
  check a list of arguments against a list of types

  """
  if len(args) != len(expected_types):
    raise Exception("the number of arguments do not match: " + str(args) + ", " + str(expected_types))
  else:
    success = True

    for a, t in zip(args, expected_types):
      t = type_check(a, t, type_definitions, parameters)
      if not t:
        success = False

    return success


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
  procedure_signatures = procedure_signatures_from_ast(procedure_sig_asts)

  type_signatures = {}

  for k,v in procedure_signatures.items():
    if k in type_signatures:
      raise Exception("duplicate type signature for " + k + " "  + str(v))
    else:
      type_signatures[k] = v

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

  procedures = {}
  for proc in procedure_asts:
    name = proc['procedure_name']
    procedures[name] = procedure_from_ast(proc, type_definitions, type_signatures)

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
  type_defs = dict([])

  for item in ast:
    name = item['type_def_name']
    k = item.keys()

    if "disj_types" in k:
      # disjunction of types
      e = {"name": name, "sort": "disj_types", "types": item['disj_types'].asList() }
    elif "disj_atoms" in k:
      # disjunction of atoms
      e = {"name": name, "sort": "disj_atoms", "atoms": item['disj_atoms'].asList() }
    elif 'range' in k:
      # range type
      minimum = integer_from_ast(item['range']['min'])
      maximum = integer_from_ast(item['range']['max'])
      e = {"name": name, "sort": "range", "min": minimum, "max": maximum }
    else:
      raise Exception("type definition is invalid!")

    type_defs[name] = e
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

        ptype = a['percept_type']
        if ptype in ['durative', 'discrete', 'special_action']:
          psort = 'action'
        elif ptype in ['percept', 'belief']:
          psort = 'percept'
        else:
          raise Exception("unrecognised percept type")

        sigs[ e['head'] ] = { 'percept_type': a['percept_type'], 'type': t, 'sort': psort }
  return sigs

def procedure_from_ast(procedure_ast, type_definitions, type_signatures):
  name = procedure_ast["procedure_name"]
  input_types = type_signatures[name]['type']

  if "parameters" in procedure_ast:
    parameters = procedure_parameters_from_ast(procedure_ast["parameters"])
  else:
    parameters = []

  if len(input_types) != len(parameters):
    raise Exception("the type signature and the definition for " + name + \
                    " have different numbers of terms! (" + str(input_types) + 
                    ", " + str(parameters) + ")")
  else:
    # using the procedure's type signature (input_types),
    # determine the types of the respective arguments
    parameters_with_types = []
    for p, t in zip(parameters, input_types):
      p_t = copy.copy(p)
      p_t["type"] = t
      parameters_with_types.append(p_t)

    rules = []
    for rule in procedure_ast["rules"]:
      r = rule_from_ast(rule, type_definitions, type_signatures, parameters_with_types)
      rules.append(r)

    return {"name" : name,
            "rules" : rules,
            "parameters" : parameters_with_types}


def rule_from_ast(ast, type_definitions, type_signatures, parameters):
  guard_conditions = [cond_from_ast(cond, type_definitions, type_signatures, parameters) for cond in ast['guard_conditions']]

  if "while_conditions" in ast:
    while_conditions = [cond_from_ast(cond, type_definitions, type_signatures, parameters) for cond in ast['while_conditions']]
  else:
    while_conditions = [NOT_TRUE]

  if "while_minimum" in ast:
    while_minimum = float_from_ast(ast['while_minimum'])
  else:
    while_minimum = 0

  if "until_conditions" in ast:
    until_conditions = [cond_from_ast(cond, type_definitions, type_signatures, parameters) for cond in ast['until_conditions']]
  else:
    until_conditions = [NOT_TRUE]

  if "until_minimum" in ast:
    until_minimum = float_from_ast(ast['until_minimum'])
  else:
    until_minimum = 0

  if ast['actions'][0] == "()":
    actions = []
  else:
    actions = [action_from_ast(action, type_definitions, type_signatures, parameters) for action in ast['actions']]

  return { "guard_conditions" : guard_conditions,
           "while_conditions" : while_conditions,
           "while_minimum" : while_minimum,
           "until_conditions" : until_conditions,
           "until_minimum" : until_minimum,
           "actions" : actions }


def cond_from_ast(ast, type_definitions, type_signatures, parameters):
  if "negation" in ast.keys():
    # it's a negation of a predicate
    inner_predicate = cond_from_ast(ast['negation'], type_definitions, type_signatures, parameters)
    return {"sort" : "negation", "predicate" : inner_predicate}

  elif "head" in ast.keys():
    # it's a predicate
    return predicate_from_ast(ast, type_definitions, type_signatures, parameters)

  elif "operator" in ast:
    # it's a binary comparison
    arg1 = expression_from_ast(ast["arg1"], type_definitions, type_signatures, parameters)
    arg2 = expression_from_ast(ast["arg2"], type_definitions, type_signatures, parameters)
    return {"sort":"binary_condition", "operator":ast["operator"], "arg1":arg1, "arg2":arg2}

  else:
    raise Exception(str(ast) + " is not a predicate, negation or binary comparison!")


def action_from_ast(ast, type_definitions, type_signatures, parameters):
  if ast == "()":
    return {}

  elif "head" in ast.keys(): #it is a predicate
    head_sort = type_signatures[ast['head']]['sort']

    if head_sort == 'procedure':
      # it's a procedure call
      p = predicate_from_ast(ast, type_definitions, type_signatures, parameters)
      p['sort'] = "proc_call"
      return p

    elif head_sort == 'action':
      # it's an action
      p = predicate_from_ast(ast, type_definitions, type_signatures, parameters)
      p['sort'] = "action"
      return p

    elif head_sort == 'percept':
      # it's a percept, oh no!
      raise Exception("the predicate " + str(ast) + " is a percept, it cannot appear" + \
                      "on the right hand side of a rule.")

    else:
      raise Exception("the predicate " + str(ast) + " is not defined as a procedure or an action")

  else:
    raise Exception(str(ast)+" does not have a type signature, it cannot feature" + \
                    "on the right hand side of a rule")


def predicate_from_ast(ast, type_definitions, type_signatures, parameters):
  if "args" in ast.keys(): # it's a predicate with args
    args = [param_from_ast(p, type_definitions, type_signatures, parameters) for p in ast["args"]]

    name = ast['head']

    if name in type_signatures:
      expected_type = type_signatures[name]['type']
    else:
      raise Exception("no type signature provided for "+name)

    tc = type_check_args(args, expected_type, type_definitions, parameters)

    if tc:
      # type check passes
      pass
    else:
      # type check fails!!
      raise Exception("the terms of the predicate " + str(ast) + \
                      " do not match its expected type " + str(expected_type))

  else: # just an atom
    args = []
  return { "sort" : "predicate", "name" : ast["head"], "terms" : args }


def expression_from_ast(ast, type_definitions, type_signatures, parameters):
  if len(ast) == 1:
    return param_from_ast(ast, type_definitions, type_signatures, parameters)
  else:
    left = expression_from_ast(ast[0], type_definitions, type_signatures, parameters)
    operator = ast[1]
    right = expression_from_ast(ast[2], type_definitions, type_signatures, parameters)
    return {"sort" : "binary_operation", "operator" : operator, "left" : left, "right" : right }


def param_from_ast(ast, type_definitions, type_signatures, parameters):
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
    return predicate_from_ast(ast, type_definitions, type_signatures, parameters)


def procedure_signatures_from_ast(ast):
  output = {}

  for a in ast:
    name = a["procedure_name"]

    if name not in output:
      if "type" in a:
        proc_type = a["type"].asList()
      else:
        proc_type = []
      output[name] = { "name" : name, "type" : proc_type, "sort" : "procedure" }

    else:
      raise Exception(name + " has a duplicate type signature!")

  return output
