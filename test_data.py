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

top_call{
facing_direction(X) ~> turn_right
true ~> turn_left
}"""

test_program3 = """
durative turn_right : (num),
         turn_left : (num)

percept facing_direction : (num)

top_call{
facing_direction(X,10) ~> turn_right
true ~> turn_left
}"""

test_program4 = """
durative turn_right : (num),
         turn_left : (num)

percept facing_direction : (num)

top_call{
facing_direction(X,10.5) ~> splodge(X)
true ~> turn_left
}"""


test_proc = """get_object{
holding & see(0,centre) ~> ()
holding & see(0,centre) ~> grab(100)
holding ~> get_to
true ~> release(1)
}"""

test_program5 = """get_object{
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
v3 = {"sort":"variable", "name":"Objective"}
v4 = {"sort":"variable", "name":"Synergy"}


p1 = {"sort":"predicate", "terms":[], "name":"foo"}

p2 = {"sort":"predicate", "terms":[], "name":"bar"}

p3 = {"sort":"predicate", "terms":[ {"sort":"predicate", "terms":[], "name":"baz"} ], "name":"foo"}

p4 = {"sort":"predicate", "terms":[ {"sort":"predicate", "terms":[], "name":"qux"} ], "name":"foo"}

p5 = {"sort":"predicate", "terms":[ v1 ], "name":"foo"}

p6 = {"sort":"predicate", "terms":[ p2 ], "name":"foo"}

p7 = {"sort":"predicate", "terms":[ v1, v2 ], "name":"blurp"}

p8 = {"sort":"predicate", "terms":[ p1, p2 ], "name":"blurp"}

p9 = {"sort":"predicate", "terms":[ v1, v1 ], "name":"blurp"}

p10 = {"sort":"predicate", "terms":[ p1, p1 ], "name":"blurp"}

