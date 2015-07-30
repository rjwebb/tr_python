#!/usr/bin/env python
# -*- coding: utf-8 -*-

import dsl_parser as dsl
import beliefstore as bs
import pedroclient
import pdb
import sys
import argparse

# Methods for sending and receiving percepts - this is the part of the 
# program that will be replaced if you choose to use ROS

def send_message(client, addr, percept_text):
  if addr is None:
    print "No agent connected"
    pass
  else:
    # send percepts
    if client.p2p(addr, percept_text) == 0:
      print "Illegal percepts message"


def get_user_input_beliefs():
  print "beliefs:",
  a = raw_input()
  beliefs = [pedroclient.PedroParser.parse(token) for token in a.split(",")]
  return [pedro_predicate_to_dict(b) for b in beliefs]


def get_beliefs_from_server(client):
  # wait for signal
  while not client.notification_ready():
    pass

  raw_message = client.get_term()
  p2pmsg = raw_message[0]
  message = p2pmsg.args[2]
  beliefs = message.toList()

  return [pedro_predicate_to_dict(b) for b in beliefs]


# Functions for formatting predicates to be sent / received to Pedro
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


# Function for grounding a predicate/variable/value with some instantiated variables
def apply_substitution(A, variables):
  if A["sort"] == "predicate" or A["sort"] == "action" or A["sort"] == "proc_call":
    new_terms = [apply_substitution(a, variables) for a in A["terms"]]
    return {"name" : A["name"], "terms": new_terms, "sort" : A["sort"]}
  elif A["sort"] == "variable":
    if A["name"] in variables:
      return variables[A["name"]]
    else:
      return A
  elif A["sort"] == "value":
    return A
  else:
    raise Exception("what is "+ str(A) + " ?")


# Function that is called when actions are performed
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
      send_message(client, server_name, cmd)


# Evaluates the rules for a particular procedure to determine which rule to fire
def get_action(belief_store, rules, variables):
  for i, rule in enumerate(rules):
    success, output = bs.evaluate_conditions(rule['conds'], belief_store, variables)
    if success:
      return i, output
  raise Exception("no-firable-rule")


def get_percepts(use_pedro, client=None):
  if use_pedro:
    percepts = get_beliefs_from_server(client)
  else:
    percepts = get_user_input_beliefs()
  return percepts


# Given a procedure, a list of values corresponding to the arguments of a procedure,
# and the procedure's type signature, return the instantiated variables
def instantiate_procedure_variables(procedure, arguments):
  parameters = procedure["parameters"]
  if len(parameters) == len(arguments):
    variables = {}
    for i, a in enumerate(arguments):
      parameter = parameters[i]
      print i, a, parameter["name"], parameter["type"]
      variables[parameter["name"]] = a
    return variables
  else:
    raise Exception("Number of parameters " + str(parameters) + " passed to the procedure "+ procedure["name"] + " is incorrect!")


def is_integer(s):
  try:
    int(s)
    return True
  except ValueError:
    return False

def is_float(s):
  try:
    float(s)
    return True
  except ValueError:
    return False


def from_raw_parameters(raw_parameters):
  out = []
  for p in raw_parameters:
    if is_integer(p):
      t = "integer"
      o = int(p)
    elif is_float(p):
      t = "float"
      o = float(p)
    elif type(p) == str:
      t = "string"
      o = p
    else:
      raise Exception("Not sure what type of parameter this is" + str(p))
    out.append( { "sort" : "value", "value" : o, "type" : t } )
  return out

# The TR algorithm
def run(task_call, program, raw_parameters, max_dp=10, use_pedro=False, shell_name=None, server_name=None):
  procedures = program['procedures']
  parameters = from_raw_parameters(raw_parameters)

  # 1. initialise variables
  LActs = {}
  FrdRules = {}

  index = 1
  called_proc_name = task_call
  original_variables = instantiate_procedure_variables(procedures[called_proc_name], parameters)
  variables = original_variables
  print "calling the procedure",called_proc_name,"with variables", str(variables)

  if use_pedro:
    client = pedroclient.PedroClient()
    c = client.register(shell_name)
    print "registered?  "+ str(c)

    client.p2p(server_name, "initialise_")
  else:
    client = None

  percepts = get_percepts(use_pedro, client=client)
  remembered_beliefs = []
  belief_store = percepts + remembered_beliefs
  #print belief_store
  # 2. while the maximum call depth has not been reached
  while index <= max_dp:
    # 3. Evaluate the guards for the rules for Call in turn,
    # to find the first rule with an inferable guard

    # get the rules for the called procedure
    rules = procedures[called_proc_name]['rules']

    R, Theta = get_action(belief_store, rules, variables)

    applied_rule = rules[R]
    A = applied_rule['actions']

    ATheta = [apply_substitution(a, Theta) for a in A]

    if len(ATheta) == 0:
      pass
    elif ATheta[0]["sort"] == "proc_call":
      called_proc_name = ATheta[0]["name"]
      arguments = ATheta[0]["terms"]
      variables = instantiate_procedure_variables(procedures[called_proc_name], arguments)
      print "calling the procedure",called_proc_name,"with variables", str(variables)

      index += 1
    else:
      ATheta_controls_only = []
      
      # for carrying out special actions
      for a in ATheta:
        if a["name"] == "remember":
          t = a["terms"][0]
          print "remember the term", str(t)
          if t not in remembered_beliefs:
            remembered_beliefs.append(t)
        elif a["name"] == "forget":
          t = a["terms"][0]          
          print "forget the term", str(t)
          if t in remembered_beliefs:
            remembered_beliefs.remove(t)
        else:
          ATheta_controls_only.append(a)
      
      # Compute controls CActs using actions of ATheta and Acts
      CActs = [predicate_to_string(a) for a in ATheta_controls_only]
      #print R, CActs
      
      # Execute CActs
      execute(CActs, LActs, use_pedro=True, \
              client=client, server_name=server_name)

      # update LActs to the set of actions in ATheta
      LActs = CActs

      # Wait for a BeliefStore update
      percepts = get_percepts(use_pedro, client=client)
      belief_store = percepts + remembered_beliefs
      
      #print belief_store

      # Go back to the top of the program
      index = 1
      called_proc_name = task_call
      variables = original_variables

  # 3. loop exited, must have reached max call depth
  if index > max_dp:
    raise Exception("call-depth-reached")

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Run a teleo-reactive program.')
  parser.add_argument('file', metavar='FILE', type=argparse.FileType('r'),
                      help='the path to the file containing the teleo-reactive program')

  parser.add_argument('task_call', metavar='TASK', default="task_call",
                   help='the name of the task to be called')
  
  parser.add_argument('params', metavar='PARAM', type=str, nargs='*',
                      help='parameters to be passed to the task call')

  args = parser.parse_args()
  program_file = args.file
  task_call = args.task_call
  print args.params
  # parameters with which to call the first method
  parameters = args.params

  program_raw = program_file.read()
  program_file.close()

  parsed_program = dsl.program.parseString(program_raw)

  program = dsl.program_from_ast(parsed_program)

  print program
  print "..."
  shell_name = "tr_python2"
  server_name = "asteroids"

  run(task_call, program, parameters, use_pedro=True, shell_name=shell_name, server_name=server_name)

