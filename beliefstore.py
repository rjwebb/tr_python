import operator
import pdb

COMPARISON_FUNCTIONS = {
  ">" : operator.gt,
  ">=" : operator.ge,
  "==" : operator.eq,
  "<=" : operator.le,
  "<" : operator.lt
}

BINARY_OPERATIONS = {
  "+" : operator.add,
  "-" : operator.sub,
  "*" : operator.mul,
  "/" : operator.div
}

def merge_dicts(*dict_args):
  """
  Given any number of dicts, shallow copy and merge into a new dict,
  precedence goes to key value pairs in latter dicts.
  """

  result = {}
  for dictionary in dict_args:
    result.update(dictionary)
  return result



def evaluate_condition_tree(condition, belief_store, variables):
  success, substitutions = eval_condition(condition, belief_store, variables)

  if success:
    return True, substitutions[0]
  else:
    return False, None

def eval_condition(cond, belief_store, variables):
  """
  Evaluate one condition

  cond -- the condition to be queried
  belief_store -- the set of percepts (facts) to query over
  variables -- (partial) instantiation of the variables in the conditions
  """

  if cond['sort'] == 'conjunction':
    return evaluate_conjunction(cond, belief_store, variables)
  # the condition is a negation-as-failure
  elif cond['sort'] == 'negation':
    return evaluate_negation(cond, belief_store, variables)

  # the condition is a predicate
  elif cond['sort'] == 'predicate':
    if cond['name'] == 'true':
      # trivially true
      return True, [variables] # success, no instantiations
    else:
      results = [pattern_match(cond, e, variables) for e in belief_store]
      substitutions = [output for (success, output) in results if success]
      print cond, substitutions
      if len(substitutions) > 0:
        return True, substitutions
      else:
        return False, None

  # the condition is a binary condition (e.g. 3 > 2, X <= 1)
  elif cond['sort'] == "binary_condition":
    comp = evaluate_binary_comparison(cond, variables)
    if comp:
      return True, [variables]
    else:
      return False, None

  # unrecognised input
  else:
    raise Exception("I don't know what this thing is: " + str(cond) )
    return False, None


def evaluate_conjunction(cond, belief_store, variables):
  cond_left = cond['left']
  cond_right = cond['right']

  success, substitutions = eval_condition(cond_left, belief_store, variables)
  if success:
    output_variables = []

    for subst in substitutions:
      updated_variables = merge_dicts(variables, subst)
      success2, variables2 = eval_condition(cond_right, belief_store, updated_variables)
      if success2:
        output_variables.extend(variables2)

    if len(output_variables) > 0:
      return True, output_variables
    else:
      return False, None
  else:
    return False, None




def evaluate_negation(cond, belief_store, variables):
  """
  Evaluates a negation as failure condition
  """

  inner_cond = cond['predicate']
  success, substitutions = eval_condition(inner_cond, belief_store, variables)
  if not success:
    return True, [variables]
  else:
    return False, None


def evaluate_binary_comparison(cond, variables):
  """
  Evaluates a binary comparison condition
  """

  arg1 = evaluate_expression(cond["arg1"], variables)
  arg2 = evaluate_expression(cond["arg2"], variables)
  op = COMPARISON_FUNCTIONS[cond['operator']]
  comp = op(arg1, arg2)

  return comp != 0

def evaluate_expression(p, variables):
  """
  Evaluate a boolean expression

  p -- the boolean expression
  variables -- instantiation of variables,
    i.e. mapping from variable names to values
  """

  if p["sort"] == "binary_operation":
    left = evaluate_expression(p['left'], variables)
    right = evaluate_expression(p['right'], variables)
    func = BINARY_OPERATIONS[p['operator']]
    return func(left, right)
  elif p["sort"] == "variable":
    v = variables[p["name"]]
    return evaluate_expression(v, variables)
  elif p["sort"] == "value":
    return p["value"]
  else:
    raise Exception(str(p) + " isn't an expression")


def pattern_match(pred_input, pred_ground, variables):
  """
  Returns a variable instantiation that causes pred_input to match with pred_ground
  This is a less powerful method than unification, because it requires that pred_ground be ground

  pred_input -- the not necessarily ground input to match
  pred_ground -- the ground input to match
  variables -- instantiation of variables in pred_input
  """

  # ground input is a variable - error!
  if pred_ground['sort'] == 'variable':
    raise Exception("RHS must not be a variable!" + str(pred_ground))

  # if the input is a value
  if pred_input['sort'] == 'value' and \
     pred_ground['sort'] == 'value' and \
     pred_input['value'] == pred_ground['value']:
    success, result = True, variables

  # input is a variable
  elif pred_input['sort'] == 'variable':
    success, result = match_variable_with_predicate(pred_input, pred_ground, variables)

  # if the input is a predicate
  elif pred_input['sort'] == 'predicate' and \
       pred_input['name'] == pred_ground['name']:
    # heads match
    success, result = match_bodies(pred_input['terms'], pred_ground['terms'], variables)

  # the inputs don't match
  else:
    success, result = False, None

  return success, result


def match_variable_with_predicate(var, pred, variables):
  """
  Returns a variable instantiation that causes the variable var to match with pred

  var -- the variable to match
  pred -- ground input to match
  variables -- instantiation of variables in pred_input
  """

  if var['name'] in variables:
    # variable is instantiated
    success, output = pattern_match(variables[var['name']], pred, variables=variables)

  else:
    # variable not yet instantiated, set it to pred
    variables2 = variables.copy()
    variables2[var['name']] = pred
    success, output = True, variables2

  return success, output

def match_bodies(input_terms, ground_terms, variables):
  """
  Match the bodies of all of the terms in the two input lists with each other

  input_terms -- not necessarily ground terms
  ground_terms -- ground terms
  variables -- variable instantiations
  """

  if len(input_terms) == len(ground_terms):
    # bodies have the same number of terms
    variables_iter = variables
    matched = True

    for k1, k2 in zip(input_terms, ground_terms):
      # iterate over the items in the respective bodies
      success,result = pattern_match(k1, k2, variables_iter)
      if not success:
        # fail, body terms don't match
        matched = False
      else:
        # update variable binding
        variables_iter = result

    if matched:
      success, result = True, variables_iter
    else:
      success, result = False, None

  else:
    # fail, bodies don't have the same number of terms
    success, result = False, None

  return success, result


if __name__=="__main__":
  test()
