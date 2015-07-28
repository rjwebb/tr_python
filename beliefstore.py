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
  '''
  Given any number of dicts, shallow copy and merge into a new dict,
  precedence goes to key value pairs in latter dicts.
  '''
  result = {}
  for dictionary in dict_args:
    result.update(dictionary)
  return result

# Evaluate a list of conditions (queries), with backtracking
def evaluate_conditions(conds, belief_store, variables):
  if conds == []:
    return True, variables
  else:
    cond = conds[0]
    success, substitutions = eval_condition(cond, belief_store, variables)

    if success:
      i = 0
      done = False
      while i < len(substitutions) and not done:
        updated_variables = merge_dicts(variables, substitutions[i])
        success2, variables2 = evaluate_conditions(conds[1:], belief_store, updated_variables)
        if success2:
          done = True
        i += 1
      if done:
        return True, variables2
      else:
        return False, None
    else:
      return False, None

# Evaluate one condition
def eval_condition(cond, belief_store, variables):
  if cond['sort'] == 'negation':
    inner_cond = cond['predicate']

    success, substitutions = eval_condition(inner_cond, belief_store, variables)
    print "negation of ", inner_cond
    print success
    if not success:
      return True, [variables]
    else:
      return False, None
  elif cond['sort'] == 'predicate':
    if cond['name'] == 'true':
      return True, [variables] # success, no instantiations
    else:
      substitutions = []

      for e in belief_store:
        success, output = pattern_match(cond, e, variables)
        if success:
          substitutions.append(output)
      
      if len(substitutions) > 0:
        return True, substitutions
      else:
        return False, None
  elif cond['sort'] == "binary_condition":
    arg1 = evaluate_expression(cond["arg1"], variables)
    arg2 = evaluate_expression(cond["arg2"], variables)
    op = COMPARISON_FUNCTIONS[cond['operator']]
    comp = op(arg1, arg2)
    if comp == 0:
      return False, None
    else:
      return True, [variables]
  else:
    raise Exception("I don't know what this thing is: " + str(cond) )
    return False, None


def evaluate_expression(p, variables):
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

"""
this is like unification, but you will never have to match a variable with
a variable because the BeliefStore is always ground??
"""
def pattern_match(pred_input, pred_ground, variables):
  if pred_ground['sort'] == 'variable':
    raise Exception("RHS must not be a variable!! oh no")

  if pred_input['sort'] == 'variable':
    success, result = match_variable_with_predicate(pred_input, pred_ground, variables)
  # if the input is a predicate
  elif pred_input['name'] == pred_ground['name']:
    # heads match
    success, result = match_bodies(pred_input['terms'], pred_ground['terms'], variables)
  else:
    # heads don't match - fail
    success, result = False, None
  return success, result

def match_variable_with_predicate(var, pred, variables):
  if var['name'] in variables:
    success, output = pattern_match(variables[var['name']], pred, variables=variables)
  else:
    variables2 = variables.copy()
    variables2[var['name']] = pred
    success, output = True, variables2
  return success, output

def match_bodies(input_terms, ground_terms, variables):
  if len(input_terms) == len(ground_terms):
    # bodies have the same number of terms
    variables_iter = variables
    matched = True
    for k1, k2 in zip(input_terms, ground_terms):
      # iterate over the items in the respective bodies
      success,result = pattern_match(k1, k2, variables_iter)
      if not success:
        # body terms don't match - fail
        matched = False
      else:
        # update variable binding
        variables_iter = result

    if matched:
      success, result = True, variables_iter
    else:
      success, result = False, None
  else:
    # bodies don't have the same number of terms - fail
    # print "predicates have a different number of terms"
    success, result = False, None

  return success, result


def test():
  import test_data as td
  print "Running unit tests for beliefstore.py"

  for p in td.ground_preds:
    for v in (td.variable_preds + td.variables):
      t, a = pattern_match(v, p, {})
      print td.format_data(v)
      print td.format_data(p)
      if a:
        print dict([(e1, td.format_data(e2)) for (e1, e2) in a.items()])
      else:
        print "No match"
      print ""

if __name__=="__main__":
  test()
