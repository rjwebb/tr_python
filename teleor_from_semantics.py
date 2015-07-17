#!/usr/bin/env python
# -*- coding: utf-8 -*-

import dsl_parser as dsl
import beliefstore as bs
import pedroclient
import pdb
import test_data

def merge_dicts(*dict_args):
  '''
  Given any number of dicts, shallow copy and merge into a new dict,
  precedence goes to key value pairs in latter dicts.
  '''
  result = {}
  for dictionary in dict_args:
    result.update(dictionary)
  return result

def apply_substitution(A, Theta):
  out = []
  for a in A:
    out.append(predicate_to_string(A[0]))
  return out

def send_message(client, addr, percept_text):
  if addr is None:
    print "No agent connected"
    pass
  else:
    # send percepts
    if client.p2p(addr, percept_text) == 0:
      print "Illegal percepts message"

def predicate_to_string(pred):
  if pred["sort"] == "predicate" or pred["sort"] == "action":
    if len(pred["terms"]) == 0:
      out = pred["name"]
    else:
      out = pred['name'] + "(" + ",".join([predicate_to_string(p) for p in pred['terms']]) + ")"
  elif pred["sort"] == "variable":
    out = pred["name"]
  elif pred["sort"] == "value":
    out = pred["value"]
  else:
    raise Exception("not sure what this is: " + str(pred))
  return out

def execute(CActs, LActs, use_pedro=False, client=None, server_name=None):
  cmds = []
  if use_pedro:
    for a in LActs:
      if a not in CActs:
        cmds.append("stop_("+a+")")
    for a in CActs:
      if a not in LActs:
        cmds.append("start_("+a+")")

    if len(cmds) > 0:
      cmd = "controls(["+",".join(cmds)+"])"
      print cmd
      send_message(client, server_name, cmd)


def eval_cond(cond, belief_store, variables):
  # condition is an atom
  if cond['sort'] == 'predicate':
    if cond['name'] == 'true':
      return True, {} # success, no instantiations
    else:
      print "evaluating:", cond['name'], cond['terms']

      substitutions = []

      for e in belief_store:
        success, output = bs.pattern_match(cond, e, variables)
        if success:
          substitutions.append(output)
          #return success, output

      if len(substitutions) > 0:
        return True, substitutions
      else:
        return False, None
  else:
    # this is where i would put rules for stuff like comparisons, haven't done this yet though! lol
    return False, None

def eval_conds(conds, belief_store, variables):
  if conds == []:
    return True, variables
  else:
    cond = conds[0]
    success, substitutions = eval_cond(cond, belief_store, variables)
    print success, substitutions

    if success:
      i = 0
      done = False
      while i < len(substitutions) and not done:
        updated_variables = merge_dicts(variables, substitutions[i])
        success2, variables2 = eval_conds(conds[1:], belief_store, updated_variables)
        if success2:
          done = True
        i += 1
      if done:
        return True, variables2
    else:
      return False, None


def get_action(belief_store, rules):
  for i, rule in enumerate(rules):
    success, output = eval_conds(rule['conds'], belief_store, {})
    if success:
      return i, output
  """    satisfied = True
    for cond in rule['conds']:
      success, output = eval_cond(cond, belief_store)
      if not success:
        print "fail"
        satisfied = False
      else:
        print output

    if satisfied:
      return i, {}"""

  raise Exception("no-firable-rule")


def get_user_input_beliefs():
  print "beliefs:",
  a = raw_input()
  return [token.strip() for token in a.split(",")]


def get_beliefs_from_server(client):
  # not doing sophisticated thread stuff yet lol
  while not client.notification_ready():
    pass

  raw_message = client.get_term()
  p2pmsg = raw_message[0]
  message = p2pmsg.args[2]
  beliefs = message.toList()

  output = munge_beliefs_from_server(beliefs)
  return output

def pedro_predicate_to_dict(pred):
  ptype = type(pred)
  if ptype == pedroclient.PStruct:
    children = [pedro_predicate_to_dict(p) for p in pred.args]
    return {"name" : pred.functor.val, "terms" : children, "sort" : "predicate" }
  elif ptype == pedroclient.PAtom:
    return {"name" : pred.val, "terms" : [], "sort" : "predicate"}
  else:
    if ptype == pedroclient.PInteger:
      t = "integer"
    elif ptype == pedroclient.PFloat:
      t = "float"
    elif ptype == pedroclient.PString:
      t = "string"
    else:
      raise Exception(str(pred) + "is of unrecognised type!")
    return {"sort" : "value", "value" : pred.val, "type" : t}

def munge_beliefs_from_server(beliefs):
  return [pedro_predicate_to_dict(b) for b in beliefs]

def run(task_call, max_dp, program, use_pedro=False):
  procedures = program['procedures']

  # 1. initialise variables
  LActs = {}
  FrdRules = {}
  index = 1
  call = task_call

  if use_pedro:
    shell_name = "tr_python"
    server_name = "asteroids"
    client = pedroclient.PedroClient()
    c = client.register(shell_name)
    print "registered?  "+ str(c)

    client.p2p(server_name, "initialise_")

  if use_pedro:
    belief_store = get_beliefs_from_server(client)
  else:
    belief_store = get_user_input_beliefs()


  # 2. if call depth maximum reached
  while index <= max_dp:
    # 3. Evaluate the guards for the rules for Call in turn,
    # to find the first rule with an inferable guard
    print call
    rules = procedures[call]

    print index
    R, Theta = get_action(belief_store, rules)
    print rules
    applied_rule = rules[R]
    A = applied_rule['actions']
    Theta = {} # not implemented unification yet

    ATheta = apply_substitution(A, Theta)
#    ATheta = A
    if type(ATheta) is list:
      # Compute controls CActs using actions of ATheta and Acts
      CActs = ATheta

      # Execute CActs
      execute(CActs, LActs, use_pedro=True, \
              client=client, server_name=server_name)

      # update LActs to the set of actions in ATheta
      LActs = ATheta

      # Wait for a BeliefStore update
      if use_pedro:
        belief_store = get_beliefs_from_server(client)
      else:
        belief_store = get_user_input_beliefs()

      # After update
      index = 1
      call = task_call

      # Check all the active calls (CActs) to see if each previously
      #fired rule instance should continue,
      #beginning with the initial TaskCall entry which has Dp = 1
      # doesn't this only apply to Nilsson's TR semantics??

      # Optimisation: We can determine that rule R of Call must
      # continue if we use the truth-maintenance system
    else: # ATheta is a procedure call
      call = ATheta
      print "called procedure",call
      index += 1

  # 3. loop exited, must have reached max call depth
  if index > max_dp:
    raise Exception("call-depth-reached")

if __name__ == "__main__":
  parsed_program = dsl.program.parseString(test_data.test_program2)

  task_call = "top_call"
  program = dsl.program_from_ast(parsed_program)
  run(task_call, 10, program, use_pedro=True)
