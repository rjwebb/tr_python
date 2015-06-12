#!/usr/bin/env python
# -*- coding: utf-8 -*-

import dsl_parser as dsl

def apply_substitution(A, Theta):
  return A

def execute(CActs):
  print "Executing: ", CActs

def get_action(belief_store, rules):
  for i,(conds, action) in enumerate(rules):
    conds_in_belief_store = [c in belief_store for c in conds]
    if all(conds_in_belief_store):
      return i
  raise Exception("no-firable-rule")

def get_user_input_beliefs():
  print "beliefs:",
  a = raw_input()
  return [token.strip() for token in a.split(",")]

def run(task_call, max_dp, procedures):
  # 1. initialise variables
  LActs = {}
  FrdRules = {}
  index = 1
  call = task_call

  belief_store = get_user_input_beliefs() + ["true"]
  print call
  # 2. if call depth maximum reached
  while index <= max_dp:
    # 3. Evaluate the guards for the rules for Call in turn,
    # to find the first rule with an inferable guard
    rules = procedures[call]

    R = get_action(belief_store, rules)
    print R
    K, A = rules[R]
    Theta = {} # not implemented unification yet

    ATheta = apply_substitution(A, Theta)
    if type(ATheta) is list:
      # Compute controls CActs using actions of ATheta and Acts
      CActs = ATheta

      # Execute CActs
      execute(CActs)

      # update LActs to the set of actions in ATheta
      LActs = ATheta

      # Wait for a BeliefStore update
      print index
      belief_store = get_user_input_beliefs() + ["true"]

      # After update
      index = 1
      call = task_call

      # Check all the active calls (CActs) to see if each previously fired rule instance should continue, beginning with the initial TaskCall entry which has Dp = 1
      # ...

      # Optimisation: We can determine that rule R of Call must continue if (some thing)
    else: # ATheta is a procedure call
      call = ATheta
      print "called procedure",call
      index += 1

  # 3. loop exited, must have reached max call depth
  if index > max_dp:
    raise Exception("call-depth-reached")

def program_from_ast(ast):
  procedures = {}
  for proc in ast["procedures"]:
    procedures[proc["name"]] = procedure_from_ast(proc["rules"])
  return procedures

def procedure_from_ast(ast):
  rules = []
  for conds, actions in ast:
    p_conds = []
    for cond in conds:
      p_conds.extend(cond)


    p_actions = []
    print actions
    for action in actions:
      if type(action) is str:
        p_actions.append(action)
      else:
        p_actions.append(action.asList()[0])

    rules.append( (p_conds, p_actions) )
  return rules

if __name__ == "__main__":
  """
  procedures = {"top_call":[(["drunk_tea"], ["()"]),
                            (["tea_water_in_mug"],["drink_tea"]),
                            (["water_in_mug"], ["add_tea"]),
                            (["kettle_boiled"],["pour_water"]),
                            (["kettle_full"],["turn_on_kettle"]),
                            ([],["fill_kettle"])]}
  """
  """
  procedures = {"top_call":[(["a","b","c"], ["()"]),
                            (["b","c"],"do_a"),
                            (["c"],"do_b"),
                            ([],"do_c")],
                "do_a":    [(["a3"], ["()"]),
                            (["a2"], ["find_a3"]),
                            (["a1"], ["find_a2"]),
                            ([], ["find_a1"])],
                "do_b":    [(["b5"], ["()"]),
                            (["b4"], ["find_b5"]),
                            (["b3"], ["find_b4"]),
                            (["b2"], ["find_b3"]),
                            (["b1"], ["find_b2"]),
                            ([], ["find_b1"])],
                "do_c":    [(["c3"], ["()"]),
                            (["c2"], ["find_c3"]),
                            (["c1"], ["find_c2"]),
                            ([], ["find_c1"])]}
  """

  test_program = """top_call{
a & b & c ~> ()
b & c ~> do_a
c ~> do_b
true ~> do_c
}
do_a{
a3 ~> ()
a2 ~> find_a3
a1 ~> find_a2
true ~> find_a1
}
do_b{
b5 ~> ()
b4 ~> find_b5
b3 ~> find_b4
b2 ~> find_b3
b1 ~> find_b2
true ~> find_b1
}
do_c{
c3 ~> ()
c2 ~> find_c3
c1 ~> find_c2
true ~> find_c1
}
"""
  parsed_program = dsl.program.parseString(test_program)

  program = program_from_ast(parsed_program)
  print program
  task_call = "top_call"

  run(task_call, 10, program)
