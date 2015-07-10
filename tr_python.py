
#!/usr/bin/env python
# -*- coding: utf-8 -*-


def get_action(belief_store, rules):
  for conds, action in rules:
    conds_in_belief_store = [c in belief_store for c in conds]
    if all(conds_in_belief_store):
      return action
  raise Exception("no-firable-rule")


def run():
  belief_store = {}
  rules = [(["drunk_tea"], "()"),
           (["tea_water_in_mug"],"drink_tea"),
           (["water_in_mug"], "add_tea"),
           (["kettle_boiled"],"pour_water"),
           (["kettle_full"],"turn_on_kettle"),
           ([],"fill_kettle")]
  
  belief_sequence = [{"kettle_full"}, {"kettle_boiled"}, {"water_in_mug"}, {"tea_water_in_mug"}, {"drunk_tea"}]

  for belief_store in belief_sequence:
    action = get_action(belief_store, rules)
    print belief_store, action


if __name__ == "__main__":
  run()

