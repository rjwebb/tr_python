#!/usr/bin/env python
# -*- coding: utf-8 -*-

def get_action(belief_store, rules):
  for cond, action in rules:
    if cond == "":
      return action
    elif cond in belief_store:
      return action
  raise Exception("no-firable-rule")


def run():
  belief_store = {}
  rules = [("drunk_tea", "()"),
           ("tea_water_in_mug","drink_tea"),
           ("water_in_mug", "add_tea"),
           ("kettle_boiled","pour_water"),
           ("kettle_full","turn_on_kettle"),
           ("","fill_kettle")]
  
  action = get_action(belief_store, rules)
  print belief_store, action

  belief_store = {"kettle_full"}
  action = get_action(belief_store, rules)
  print belief_store, action

  belief_store = {"kettle_boiled"}
  action = get_action(belief_store, rules)
  print belief_store, action

  belief_store = {"water_in_mug"}
  action = get_action(belief_store, rules)
  print belief_store, action

  belief_store = {"tea_water_in_mug"}
  action = get_action(belief_store, rules)
  print belief_store, action

  belief_store = {"drunk_tea"}
  action = get_action(belief_store, rules)
  print belief_store, action

if __name__ == "__main__":
  run()
