"""
this is like unification, but you will never have to match a variable with a variable because the BeliefStore is always ground??
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
    print type(pred_input['name']), type(pred_ground['name'])
    print pred_input['name'], ",", pred_ground['name'], "are different names"
    success, result = False,None
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
    print "predicates have a different number of terms"
    success, result = False,None

  return success, result
