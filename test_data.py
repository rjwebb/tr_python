procedures = {"top_call":[(["drunk_tea"], ["()"]),
                            (["tea_water_in_mug"],["drink_tea"]),
                            (["water_in_mug"], ["add_tea"]),
                            (["kettle_boiled"],["pour_water"]),
                            (["kettle_full"],["turn_on_kettle"]),
                            ([],["fill_kettle"])]}

procedures2 = {"top_call":[(["a","b","c"], ["()"]),
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

test_program2 = """
durative turn_right : (num),
         turn_left : (num)

percept facing_direction : (num)

top_call : () ~>
top_call{
facing_direction(X) ~> turn_right
true ~> turn_left
}"""


test_program3 = """
durative turn_right : (num),
         turn_left : (num)

percept facing_direction : (num)

top_call : ~>
top_call{
facing_direction(X,10) ~> turn_right
true ~> turn_left
}"""

test_program4 = """
durative turn_right : (num),
         turn_left : (num)

percept facing_direction : (num)

top_call : () ~>
top_call{
facing_direction(X,10.5) ~> splodge(X)
true ~> turn_left
}"""


test_proc = """
discrete grab : (num),
         release : (num)

durative get_to : (),
         turn : (direction),
         move : (num)

percept holding : (),
        see : (num, direction)

get_object : () ~>
get_object{
holding & see(0,centre) ~> ()
holding & see(0,centre) ~> grab(100)
holding ~> get_to
true ~> release(1)
}

get_to : () ~>
get_to {
see(0, centre)    ~> ()
see(0, Dir)       ~> turn(Dir)
see(_, centre)    ~> move(6)
see(_, Dir)       ~> move(4) , turn(Dir)
true              ~> turn(left)
}
"""


test_program6 = """durative facing_direction : (num)
top_task{
    true ~> turn_left
}"""

test_program7 = """arm ::= arm1 | arm2
table ::= table1 | shared | table2
block ::= (1 .. 16)
place ::= table || block

percept
  holding : (arm, block),
  on : (block, place)

durative
  move : (num)

discrete
  grab : (num),
  release : (num)

get_object{
holding & see(0,centre) ~> ()
holding & see(0,centre) ~> grab(100)
holding ~> get_to
true ~> release(1)
}

get_to {
see(0, centre)    ~> ()
see(0, Dir)       ~> turn(Dir)
see(_, centre)    ~> move(6)
see(_, Dir)       ~> move(4) , turn(Dir)
true              ~> turn(left)
}
"""

test_program8 = """
durative turn_right : (num),
         turn_left : (num)

discrete shoot : (num)

percept facing_direction : (num),
        see : (string, num)

top_call : () ~>
top_call{
facing_direction(X) & X > 3.14 ~> turn_right
facing_direction(X) & X <= 3.14 ~> turn_left
true ~> shoot
}"""

test_program9 = """
durative turn_left : (),
         turn_right : (),
         move_forward : (num),
         proceed : (direction)

discrete explode : (),
         pick_up : (thing)

percept see : (thing, direction)

thing ::= box | shoe
direction ::= hither | thither | yonder

top_call : (thing, direction) ~>
top_call(Arg1, Arg2){
  see(Arg1, hither) ~> pick_up(Arg1)
  see(Arg1, thither) ~> proceed(thither)
  true ~> wander_about(Arg2)
}

wander_about : (direction) ~>
wander_about(X){
  true ~> turn_left, move_forward(0.3)
}
"""

test_program10 = """
durative turn_right : (),
         turn_left : (),
         move_forward : (),
         move_backward : (),
         nothing : ()

discrete shoot : ()

percept facing_direction : (num),
        see : (string, num)

top_call : () ~>
top_call{
see(asteroid, dead_centre, Dist) & Dist < 300 ~> move_forward, shoot
see(asteroid, left, Dist) & Dist < 300 ~> turn_left, move_forward, shoot
see(asteroid, right, Dist) & Dist < 300 ~> turn_right, move_forward, shoot
true ~> turn_right
}

shoot_at : (num) ~>
shoot_at(Dir){
facing_direction(X) & X > Dir ~> turn_right, shoot
facing_direction(X) & X < Dir ~> turn_left, shoot
true ~> shoot
}"""

test_program11 = """
durative turn_right : (),
         turn_left : (),
         move_forward : (),
         move_backward : (),
         nothing : ()

discrete shoot : ()

percept facing_direction : (num),
        see : (string, num)

top_call : () ~>
top_call{
see(asteroid, Dir, Dist) ~> shoot
true ~> ()
}

regulate_speed : (num) ~>
regulate_speed(Max){
speed(S) & S > Max ~> move_backward
true ~> move_forward
}
"""

test_typedef = """arm ::= arm1 | arm2
table ::= table1 | shared | table2
block ::= (1 .. 16)
place ::= table || block
"""

test_typesig = """percept
  holding : (arm, block),
  on : (block, place)

durative
  move : (num)
"""



v1 = {"sort":"variable", "name":"A"}
v2 = {"sort":"variable", "name":"B"}
v3 = {"sort":"variable", "name":"C"}
v4 = {"sort":"variable", "name":"D"}


pg1 = {"sort":"predicate", "terms":[], "name":"foo"}

pg2 = {"sort":"predicate", "terms":[], "name":"bar"}

pg3 = {"sort":"predicate", "terms":[ {"sort":"predicate", "terms":[], "name":"baz"} ], "name":"foo"}

pg4 = {"sort":"predicate", "terms":[ {"sort":"predicate", "terms":[], "name":"qux"} ], "name":"foo"}

pg5 = {"sort":"predicate", "terms":[ pg2 ], "name":"foo"}

pg6 = {"sort":"predicate", "terms":[ pg1, pg2 ], "name":"blurp"}

pg7 = {"sort":"predicate", "terms":[ pg1, pg1 ], "name":"blurp"}

pg8 = {"sort":"predicate", "terms":[ pg6, pg7 ], "name":"blurp"}

pg9 = {"sort":"predicate", "terms":[ pg1, pg7, pg3 ], "name":"blurp"}


pv1 = {"sort":"predicate", "terms":[ v1 ], "name":"foo"}

pv2 = {"sort":"predicate", "terms":[ v1, v2 ], "name":"blurp"}

pv3 = {"sort":"predicate", "terms":[ v1, v1 ], "name":"blurp"}

pv4 = {"sort":"predicate", "terms":[ pg1, v3, pg3], "name":"foo"}

pv5 = {"sort":"predicate", "terms":[ pg1, v3, v4], "name":"foo"}


ground_preds = [pg1, pg2, pg3, pg4, pg5, pg6, pg7, pg8, pg9]
variable_preds = [pv1, pv2, pv3, pv4, pv5]
variables = [v1, v2, v3, v4]

test_programs = [test_program, test_program2, test_program3, test_program4, test_program6, test_program7, test_program8, test_program9]


def format_data(pred):
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
