#!/usr/bin/env python
# -*- coding: utf-8 -*-

import dsl_parser as dsl
import tr_grammar as grammar
import beliefstore as bs
import pedroclient
import pdb
import sys
import argparse

try:
  import pycallgraph
  from pycallgraph import PyCallGraph
  from pycallgraph import Config
  from pycallgraph import GlobbingFilter
  from pycallgraph.output import GraphvizOutput
  PCG_AVAILABLE = True
except ImportError:
  PCG_AVAILABLE = False


"""
Using the PedroClient 'client',
send a message containing 'percept_text'
to the Pedro user 'addr'
"""
def send_message(client, addr, percept_text):
  if addr is None:
    print "No agent connected"
    pass
  else:
    # send percepts
    if client.p2p(addr, percept_text) == 0:
      print "Illegal percepts message"


"""
Return parsed beliefs, entered in at the terminal
"""
def get_user_input_beliefs():
  print "beliefs:",
  a = raw_input()
  beliefs = [pedroclient.PedroParser.parse(token) for token in a.split(",")]
  return [pedro_predicate_to_dict(b) for b in beliefs]


"""
Given an initialised PedroClient, wait for and return beliefs from the server
"""
def get_beliefs_from_server(client):
  # wait for signal
  while not client.notification_ready():
    pass

  raw_message = client.get_term()
  p2pmsg = raw_message[0]
  message = p2pmsg.args[2]
  beliefs = message.toList()

  return [pedro_predicate_to_dict(b) for b in beliefs]


"""
Converts a predicate received by Pedro into its dict representation
"""
def pedro_predicate_to_dict(pred):
  ptype = type(pred)

  if ptype == pedroclient.PStruct:
    children = [pedro_predicate_to_dict(p) for p in pred.args]
    return {"name" : pred.functor.val,
            "terms" : children,
            "sort" : "predicate" }

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


"""
Converts a predicate (as a dict) to its printed representation (a string)
"""
def predicate_to_string(pred):
  if pred["sort"] == "predicate" or pred["sort"] == "action":
    if len(pred["terms"]) == 0:
      out = pred["name"]
    else:
      out = pred['name'] + \
            "(" + \
            ",".join([predicate_to_string(p) for p in pred['terms']]) + \
            ")"
  elif pred["sort"] == "variable":
    out = pred["name"]
  elif pred["sort"] == "value":
    out = pred["value"]
  else:
    raise Exception("not sure what this is: " + str(pred))
  return out


"""
If 'A' is a list of predicates with some variables,
then this method grounds the predicates with respect to
the mapping from variable names to values in  in 'variables'
"""
def apply_substitution(A, variables):
  if A["sort"] in ["predicate", "action", "proc_call"]:
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


"""
Execute the actions contained in CActs.
Knowledge of the previously fired actions (LActs) is required.
It then sends the actions to the Pedro server
"""
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


"""
Returns the first rule that evaluates to true
rules - a list of rules
belief_store - a set of predicates (truths)
variables - a mapping from variable names to values
"""
def get_action(belief_store, rules, variables):
  for i, rule in enumerate(rules):
    # current the algorithm only evaluates guard conditions
    success, output = bs.evaluate_conditions(rule['guard_conditions'],
                                             belief_store,
                                             variables)
    if success:
      return i, output
  raise Exception("no-firable-rule")


"""
If using pedro wait for and receive new percepts from the server.
If not, request user input (by keyboard) of percepts.
"""
def get_percepts(use_pedro, client=None):
  if use_pedro:
    percepts = get_beliefs_from_server(client)
  else:
    percepts = get_user_input_beliefs()
  return percepts


"""
Given a procedure,
a list of values corresponding to the arguments of a procedure,
and the procedure's type signature,
return the instantiated variables
"""
def instantiate_procedure_variables(procedure, arguments):
  parameters = procedure["parameters"]
  if len(parameters) == len(arguments):
    variables = {}
    for i, a in enumerate(arguments):
      parameter = parameters[i]
      variables[parameter["name"]] = a
    return variables
  else:
    raise Exception("Number of parameters " + str(parameters) +
                    " passed to the procedure "+ procedure["name"] +
                    " is incorrect!")


"""
Returns true if the input can be converted to an integer
"""
def is_integer(s):
  try:
    int(s)
    return True
  except ValueError:
    return False


"""
Returns true if the input can be converted to a floating-point number
"""
def is_float(s):
  try:
    float(s)
    return True
  except ValueError:
    return False


"""
Given a list of primitive data items expressed as a strings,
convert as many as possible into integers or floats.
"""
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


"""
This procedure calls a teleo-reactive procedure and returns a list of actions.
program - the data structure describing the program to be called
call - the name of the root TR procedure to be called
parameters - a list of parameters to be passed to the procedure
max_dp - maximum number of times that procedures can recursively call each other
dp - the current recursive depth
"""
def call_procedure(program, call, parameters, belief_store,
                   max_dp=10, dp=1):
  # call depth reached exception
  if dp > max_dp:
    raise Exception("call-depth-reached")

  procedures = program['procedures']
  variables = instantiate_procedure_variables(procedures[call],
                                              parameters)

  rules = procedures[call]['rules']
  R, Theta = get_action(belief_store, rules, variables)
  A = rules[R]['actions']
  ATheta = [apply_substitution(a, Theta) for a in A]


  if len(ATheta) == 1 and ATheta[0]['sort'] == 'proc_call':
    # the returned rule involves a procedure call
    new_call = ATheta[0]['name']
    new_parameters = ATheta[0]['terms']
    new_dp = dp + 1

    return call_procedure(program, new_call, new_parameters, belief_store,
                          max_dp=max_dp, dp=new_dp)
  else:
    # the returned rule consists of a list of actions
    return A, Theta


"""
This procedure runs a teleo-reactive program.

program - the data structure describing the program to be run
task_call - the name of the root TR procedure to be called
raw_parameters - a list of strings, which are the parameters to the procedure
max_dp - maximum number of times that procedures can recursively call each other
use_pedro - whether the program should send/receive messages via Pedro
shell_name - the name the program will take when interacting using Pedro
server_name - the name of the Pedro server the program will connect to

"""
def run(program, task_call, raw_parameters,
        max_dp=10, use_pedro=False, shell_name=None, server_name=None):

  if use_pedro:
    # create a pedro client
    client = pedroclient.PedroClient()
    c = client.register(shell_name)
    print "registered?  "+ str(c)
    client.p2p(server_name, "initialise_")
  else:
    client = None

  root_parameters = from_raw_parameters(raw_parameters)
  remembered_beliefs = []

  # the set of actions called in the last cycle
  LActs = {}

  # the main operation loop, run indefinitely
  while True:
    # Prepare the BeliefStore.
    percepts = get_percepts(use_pedro, client=client)
    belief_store = percepts + remembered_beliefs

    # Get the actions that the robot must perform, as a result of calling
    # the procedure 'task_call' in 'program' with 'root_parameters'.
    actions, variables = call_procedure(program, task_call, root_parameters,
                                        belief_store, max_dp=1, dp=1)
    instantiated_actions = [apply_substitution(a, variables) for a in actions]

    # List of actions to send to the agent
    controls_to_send = []

    # Apply the 'remember' and 'forget' rules.
    for a in instantiated_actions:
      if a["name"] == "remember":
        t = a["terms"][0]
        if t not in remembered_beliefs:
          remembered_beliefs.append(t)

      elif a["name"] == "forget":
        t = a["terms"][0]
        if t in remembered_beliefs:
          remembered_beliefs.remove(t)

      else:
        controls_to_send.append(a)

    # Convert the actions to strings, to be sent to the agent
    CActs = [predicate_to_string(a) for a in controls_to_send]

    # Execute CActs.
    execute(CActs, LActs, use_pedro=True, \
            client=client, server_name=server_name)

    # update the set of last-called actions.
    LActs = CActs


if __name__ == "__main__":
  # command-line arguments
  parser = argparse.ArgumentParser(description='Run a teleo-reactive program.')
  parser.add_argument('file', metavar='FILE', type=argparse.FileType('r'),
                      help='the file containing the teleo-reactive program')

  parser.add_argument('task_call', metavar='TASK', default="task_call",
                   help='the name of the task to be called')
  parser.add_argument('params', metavar='PARAM', type=str, nargs='*',
                      help='parameters to be passed to the task call')

  parser.add_argument('--shell', dest="shell_name", type=str, default="",
                      help='the name of the agent')

  parser.add_argument('--server', dest="server_name", type=str, default="",
                      help='the name of the server')

  parser.add_argument('--graph', dest="pcg_graph",
                      action="store_true", default=False)

  args = parser.parse_args()

  # read the program file
  program_file = args.file
  program_raw = program_file.read()
  program_file.close()

  if PCG_AVAILABLE and args.pcg_graph:
    config = Config()
    config.trace_filter = GlobbingFilter(exclude=[
      'pedroclient.*',
      'Queue.*',
      'threading.*',
      'socket.*',
      'pycallgraph.*'
    ])

    parsing_graph_output = GraphvizOutput()
    parsing_graph_output.output_file = 'parsing_graph.png'

    tr_graph_output = GraphvizOutput()
    tr_graph_output.output_file = 'tr_graph.png'

  # parse the program's source code
  parsed_program = grammar.program.parseString(program_raw)

  if PCG_AVAILABLE and args.pcg_graph:
    with PyCallGraph(output=parsing_graph_output, config=config):
      program = dsl.program_from_ast(parsed_program)
  else:
    program = dsl.program_from_ast(parsed_program)


  # the name of the task to be called
  task_call = args.task_call


  # parameters with which to call the first method
  parameters = args.params


  # pedro parameters
  shell_name = args.shell_name
  server_name = args.server_name


  # run the program
  if PCG_AVAILABLE and args.pcg_graph:
    with PyCallGraph(output=tr_graph_output, config=config):

      run(program, task_call, parameters,
          use_pedro=True, shell_name=shell_name, server_name=server_name)
  else:
    run(program, task_call, parameters,
        use_pedro=True, shell_name=shell_name, server_name=server_name)
