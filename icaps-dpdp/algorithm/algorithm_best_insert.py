# Copyright (C) 2021. Huawei Technologies Co., Ltd. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE

import copy
import random

from src.common.factory import Factory
from src.common.node import Node
from src.common.order import OrderItem
from src.common.vehicle import Vehicle
from src.conf.configs import Configs
from src.utils.input_utils import get_factory_info, read_json
from src.utils.json_tools import convert_nodes_to_json
from src.utils.json_tools import get_vehicle_instance_dict, get_order_item_dict, __convert_json_to_nodes
from src.utils.json_tools import read_json_from_file, write_json_to_file
from src.utils.logging_engine import logger

from algorithm.localsearch_structs import LLNode, LLRoute, LLSolution
from algorithm.problemdata import ProblemData
from typing import List, Dict


def scheduling():
    # read the input json, you can design your own classes
    problem_data:ProblemData = __read_input_json()

    # dispatching algorithm
    solution:LLSolution = dispatch_orders_to_vehicles( problem_data )

    # convert solution to original data structure
    vehicle_id_to_destination, vehicle_id_to_planned_route = convert_solution( problem_data, solution)

    # output the dispatch result
    __output_json(vehicle_id_to_destination, vehicle_id_to_planned_route)


"""
Main algorithm
"""

# aux func to reconstruct route plan from previous iteration
def extend_LLRoute_with_node(route:LLRoute, node:Node, factory_no:int) -> list[OrderItem] :
    # delivery items
    if node.delivery_items:
        first_item:OrderItem = node.delivery_items[0]
        curr_order_id = first_item.order_id
        curr_package = []
        for item in node.delivery_items:
            if item.order_id == curr_order_id:
                curr_package.append(item)
            else:
                # create llnode and insert to end of the route
                llnode = LLNode('d', factory_no, curr_package) # for demo and naive algorithms *partner* is not required
                route.insert_node_back(llnode)
                # start new package
                curr_order_id = item.order_id
                curr_package = [item]
        # handle the rest, what's left in *curr_package* (always, if item list contains only 1 item)
        if curr_package:
            llnode = LLNode('d', factory_no, curr_package) # for demo and naive algorithms node *partner* is not required
            route.insert_node_back(llnode)
    # pickup items
    allocated_items:list[OrderItem] = []
    if node.pickup_items:
        first_item:OrderItem = node.pickup_items[0]
        curr_order_id = first_item.order_id
        curr_package = []
        for item in node.pickup_items:
            if item.order_id == curr_order_id:
                curr_package.append(item)
            else:
                # create llnode and insert to end of the route
                llnode = LLNode('p', factory_no, curr_package) # for demo and naive algorithms *partner* is not required
                route.insert_node_back(llnode)
                allocated_items.extend(curr_package)
                # start new package
                curr_order_id = item.order_id
                curr_package = [item]
        # handle the rest, what's left in *curr_package* (always, if item list contains only 1 item)
        if curr_package:
            llnode = LLNode('p', factory_no, curr_package) # for demo and naive algorithms node *partner* is not required
            route.insert_node_back(llnode)
            allocated_items.extend(curr_package)
    return allocated_items

# aux function to set partner node relationships in an *LLRoute*
def set_partner_nodes(route:LLRoute):
    stack:list[LLNode] = []
    for new_node in route.factory_nodes:
        if new_node.is_delivery and stack:
            last_node = stack[-1]
            item_list = copy.copy(new_node.items)
            item_list.reverse() # delivery item list is reversed, so we have to reverse it back
            if last_node.is_pickup and last_node.items == item_list:
                last_node.partner = new_node
                new_node.partner = last_node
                stack.pop(-1)
                continue # if partner nodes, then proceed to next node in the route
        stack.append(new_node)
    # safety check
    for node in stack:
        assert not node.is_pickup, f"pickup node left in stack"

# "best insert" dispatching method: position of P and D nodes of each package are choosen such that resulting solution minimizes current objective value 
def dispatch_orders_to_vehicles( problem_data:ProblemData ):
    
    # initializing solution
    solution = LLSolution( problem_data )

    # # step 1
    # # dealing with the vehicles, that have a destination by input
    # # note, that these vehicles may have items on board, some of which may need to be delivered to current destination
    # # firstly, creating D nodes for items, which need to be delivered to current destination (if any)
    # # secondly, creating P and D nodes for items, which need to be picked up at current destination (if any)
    # already_allocated_items = []
    # for vehicle in problem_data.vehicles:
    #     if not vehicle.destination:
    #         continue
    #     # D nodes for delivery items
    #     package_items = []
    #     for idx, item in enumerate(vehicle.destination.delivery_items):
    #         package_items.append(item)
    #         if item == vehicle.destination.delivery_items[-1] or item.order_id != vehicle.destination.delivery_items[idx+1].order_id:
    #             factory_id = item.delivery_factory_id
    #             factory_no = problem_data.factory_id_to_int[factory_id]
    #             new_node = LLNode('d', factory_no, copy.copy(package_items))
    #             solution.routes[vehicle.no].insert_node_back(new_node)
    #             package_items = []
    #     # P nodes and D nodes for pickup items
    #     package_items = []
    #     for idx, item in enumerate(vehicle.destination.pickup_items):
    #         package_items.append(item)
    #         if item == vehicle.destination.pickup_items[-1] or item.order_id != vehicle.destination.pickup_items[idx+1].order_id:
    #             p_node, d_node =__create_pickup_and_delivery_nodes_of_items(package_items, problem_data.factory_id_to_int)
    #             node_to_insert_after = solution.routes[vehicle.no].last_pickup()
    #             solution.routes[vehicle.no].insert_node_after(p_node, after=node_to_insert_after)
    #             solution.routes[vehicle.no].insert_node_after(d_node, after=p_node)
    #             already_allocated_items.extend(package_items)
    #             package_items = []

    # # step 2
    # # dealing with the items currently on board
    # # those which need to be delivered to current destination are already handled in step 1
    # # for the rest we need to create D nodes
    # for vehicle in problem_data.vehicles:
    #     unloading_sequence_of_items:List[OrderItem] = vehicle.get_unloading_sequence()
    #     if not unloading_sequence_of_items:
    #         continue
    #     package_items = []
    #     for idx, item in enumerate(unloading_sequence_of_items):
    #         if vehicle.destination and item.id in [ i.id for i in vehicle.destination.delivery_items ]:
    #             continue
    #         package_items.append(item)
    #         if item == unloading_sequence_of_items[-1] or item.order_id != unloading_sequence_of_items[idx+1].order_id:
    #             factory_id = item.delivery_factory_id
    #             factory_no = problem_data.factory_id_to_int[factory_id]
    #             new_node = LLNode('d', factory_no, copy.copy(package_items))
    #             solution.routes[vehicle.no].insert_node_back(new_node)
    #             package_items = []

    # NEW METHOD: RECONSTRUCT ROUTE PLAN FROM PREVIOUS ITERATION
    already_allocated_items = [] # items which are not on board but already in the route-plan of a vehicle
    for vehicle in problem_data.vehicles:
        vehicle_int = problem_data.vehicle_id_to_int[vehicle.id]
        # construct current route-plan as *Node* list
        route_plan:list[Node] = [vehicle.destination] if vehicle.destination else []
        route_plan.extend(vehicle.planned_route)
        # construct route-plan as *LLRoute*
        for node in route_plan:
            factory_no = problem_data.factory_id_to_int[node.id]
            just_allocated:list[OrderItem] = extend_LLRoute_with_node(solution.routes[vehicle_int], node, factory_no)
            already_allocated_items.extend([item.id for item in just_allocated])
        set_partner_nodes(solution.routes[vehicle_int])

    # step 3
    # dispatch unallocated orders to vehicles
    capacity = problem_data.vehicles[0].board_capacity # all the vehicles have the same capacity

    # link orders and order items
    order_id_to_items:Dict[str, List[OrderItem]] = {}
    for item in problem_data.unallocated_order_items:
        if item.id in already_allocated_items:
            continue
        if item.order_id not in order_id_to_items:
            order_id_to_items[item.order_id] = []
        order_id_to_items[item.order_id].append(item)

    # allocate orders to vehicles
    for items in order_id_to_items.values():
        demand = __calculate_demand(items)

        # order exceeds the capacity limit
        # partition order items to separate packages
        if demand > capacity:

            cur_demand = 0
            tmp_items = []
            for item in items:
                if cur_demand + item.demand > capacity:

                    pickup_node, delivery_node = __create_pickup_and_delivery_nodes_of_items(tmp_items, problem_data.factory_id_to_int)
                    score, vehicle, p_node_after, d_node_after = find_best_insert(problem_data, solution, pickup_node, delivery_node)
                    solution.routes[vehicle.no].insert_node_after(pickup_node, after=p_node_after)
                    solution.routes[vehicle.no].insert_node_after(delivery_node, after=d_node_after)

                    tmp_items = []
                    cur_demand = 0

                tmp_items.append(item)
                cur_demand += item.demand

            if len(tmp_items) > 0:
                pickup_node, delivery_node = __create_pickup_and_delivery_nodes_of_items(tmp_items, problem_data.factory_id_to_int)
                score, vehicle, p_node_after, d_node_after = find_best_insert(problem_data, solution, pickup_node, delivery_node)
                solution.routes[vehicle.no].insert_node_after(pickup_node, after=p_node_after)
                solution.routes[vehicle.no].insert_node_after(delivery_node, after=d_node_after)
        
        # order is within the capacity limit
        else:
            pickup_node, delivery_node = __create_pickup_and_delivery_nodes_of_items(items, problem_data.factory_id_to_int)
            score, vehicle, p_node_after, d_node_after = find_best_insert(problem_data, solution, pickup_node, delivery_node)
            solution.routes[vehicle.no].insert_node_after(pickup_node, after=p_node_after)
            solution.routes[vehicle.no].insert_node_after(delivery_node, after=d_node_after)

    return solution


def __create_pickup_and_delivery_nodes_of_items(items: list, factory_id_to_int: dict):
    
    pickup_factory_id = __get_pickup_factory_id(items)
    delivery_factory_id = __get_delivery_factory_id(items)
    if len(pickup_factory_id) == 0 or len(delivery_factory_id) == 0:
        return None, None

    pickup_node = LLNode('p', factory_id_to_int[pickup_factory_id], copy.copy(items))
    items.reverse()
    delivery_node = LLNode('d', factory_id_to_int[delivery_factory_id], copy.copy(items))
    pickup_node.partner = delivery_node
    delivery_node.partner = pickup_node

    return pickup_node, delivery_node


def find_best_insert( pdata:ProblemData, solution:LLSolution, pickup_node:LLNode, delivery_node:LLNode ) -> tuple[float, Vehicle, LLNode, LLNode]:
    possible_inserts:List[tuple] = []
    for vehicle in pdata.vehicles:
        route:LLRoute = solution.routes[vehicle.no]
        current_node_1 = route.begin
        while current_node_1 != route.end:
            route.insert_node_after(pickup_node, after=current_node_1)
            current_node_2 = pickup_node
            while current_node_2 != route.end:
                route.insert_node_after(delivery_node, after=current_node_2)
                if solution.check_vehicle_route_constraints(vehicle):
                    score = solution.evaluate()
                    possible_inserts.append( (score, vehicle, current_node_1, current_node_2) )
                delivery_node.remove()
                current_node_2 = current_node_2.succ
            pickup_node.remove()
            current_node_1 = current_node_1.succ

    # choosing strategy: first from all optimal
    best_insert:tuple = possible_inserts[0]
    for ins in possible_inserts:
        if ins[0] < best_insert[0]: # <= if choosing strategy is last from all optimal
            best_insert = ins

    # choosing strategy: random from all optimal
    # best_score = min( [ ins[0] for ins in possible_inserts ] )
    # optimal_inserts = [ ins for ins in possible_inserts if ins[0] == best_score]
    # best_insert:tuple = random.choice(optimal_inserts)

    return best_insert[0], best_insert[1], best_insert[2], best_insert[3]


"""
Data interaction
"""

def __read_input_json():
    # read factory info
    id_to_factory = get_factory_info(Configs.factory_info_file_path)

    # read route info
    distance_mtx = read_json(Configs.distance_mtx_file_path)
    time_mtx = read_json(Configs.time_mtx_file_path)
    route_info = { 'distance': distance_mtx, 'time': time_mtx }

    # read current input
    unallocated_order_items = read_json_from_file(Configs.algorithm_unallocated_order_items_input_path)
    id_to_unallocated_order_item = get_order_item_dict(unallocated_order_items, 'OrderItem')

    ongoing_order_items = read_json_from_file(Configs.algorithm_ongoing_order_items_input_path)
    id_to_ongoing_order_item = get_order_item_dict(ongoing_order_items, 'OrderItem')

    id_to_order_item = {**id_to_unallocated_order_item, **id_to_ongoing_order_item}

    vehicle_infos = read_json_from_file(Configs.algorithm_vehicle_input_info_path)
    id_to_vehicle = get_vehicle_instance_dict(vehicle_infos, id_to_order_item, id_to_factory)

    problem_data = ProblemData( id_to_factory, route_info, id_to_unallocated_order_item, id_to_vehicle )

    # read instance number
    with open(Configs.current_instance_file_path, 'r') as f:
            curr_instance = f.read()
    problem_data.current_instance = curr_instance

    # read previous planned route of vehicles (only from the second iteration)
    with open(Configs.first_iteration_flag_file_path, 'r') as f:
            first_iteration_flag = int(f.read()) # int() is crucial
    if first_iteration_flag: # toggle flag in the first iteration
        with open(Configs.first_iteration_flag_file_path, 'w') as f:
            f.write('0')
    else: # read previous planned routes
        vehicle_id_to_planned_route_from_json = read_json_from_file(Configs.algorithm_output_planned_route_path)
        vehicle_id_to_planned_route = __convert_json_to_nodes(vehicle_id_to_planned_route_from_json, id_to_order_item)
        for vehicle in problem_data.vehicles:
            # set planned route from input (except if there's no destination, which means planned route is already obsolete)
            vehicle.planned_route = vehicle_id_to_planned_route[vehicle.id] if vehicle.destination else []
            # update planned route: remove nodes that have become obsolete since the last decision point
            for idx, node in enumerate(vehicle.planned_route):
                # check if *node* is the destination node
                if node.delivery_items != vehicle.destination.delivery_items:
                    continue
                if node.pickup_items != vehicle.destination.pickup_items:
                    continue
                # *node* is the destination node -> remove it and preceeding nodes from the list
                vehicle.planned_route = vehicle.planned_route[idx+1:]

    return problem_data


def convert_solution( problem_data:ProblemData, solution:LLSolution ):
    
    # convert solution to the original data structure
    vehicle_id_to_planned_route:Dict[str, List[Node]] = {}
    for idx, route in enumerate(solution.routes):
        node_list = []
        for llnode in route.factory_nodes:
            factory_id = problem_data.factories[llnode.factory].id
            pickup_list = llnode.items if llnode.is_pickup else []
            delivery_list = llnode.items if llnode.is_delivery else []
            node = Node( factory_id, 0, 0, pickup_list, delivery_list )
            node_list.append(node)
        vehicle_id = problem_data.vehicles[idx].id
        vehicle_id_to_planned_route[vehicle_id] = node_list

    # partition routes of solution to destination and planned route
    vehicle_id_to_destination:Dict[str, Node] = {}
    for vehicle in problem_data.vehicles:
        full_route:List[Node] = vehicle_id_to_planned_route.get(vehicle.id)

        # combine adjacent nodes with the same factory
        __combine_duplicated_nodes(full_route)

        # determine the destination and the planned route
        destination = None
        planned_route = []
        if vehicle.destination is not None:
            if len(full_route) == 0:
                logger.error(f"Planned route of vehicle {vehicle.id} is wrong")
            else:
                destination = full_route[0]
                destination.arrive_time = vehicle.destination.arrive_time
                planned_route = full_route[1:]
        elif len(full_route) > 0:
            destination = full_route[0]
            planned_route = full_route[1:]
        vehicle_id_to_destination[vehicle.id] = destination
        vehicle_id_to_planned_route[vehicle.id] = planned_route

    return vehicle_id_to_destination, vehicle_id_to_planned_route


def __output_json(vehicle_id_to_destination, vehicle_id_to_planned_route):
    write_json_to_file(Configs.algorithm_output_destination_path, convert_nodes_to_json(vehicle_id_to_destination))
    write_json_to_file(Configs.algorithm_output_planned_route_path, convert_nodes_to_json(vehicle_id_to_planned_route))


"""
Auxiliary functions
"""

def __calculate_demand(item_list:List[OrderItem]):
    demand = 0
    for item in item_list:
        demand += item.demand
    return demand


def __get_pickup_factory_id(items:List[OrderItem]):
    if len(items) == 0:
        logger.error("Length of items is 0")
        return ""

    factory_id = items[0].pickup_factory_id
    for item in items:
        if item.pickup_factory_id != factory_id:
            logger.error("The pickup factory of these items is not the same")
            return ""

    return factory_id


def __get_delivery_factory_id(items:List[OrderItem]):
    if len(items) == 0:
        logger.error("Length of items is 0")
        return ""

    factory_id = items[0].delivery_factory_id
    for item in items:
        if item.delivery_factory_id != factory_id:
            logger.error("The delivery factory of these items is not the same")
            return ""

    return factory_id


# join adjacent nodes of the same location
def __combine_duplicated_nodes(nodes:List[Node]):
    n = 0
    while n < len(nodes)-1:
        if nodes[n].id == nodes[n+1].id:
            duplicated_node = nodes.pop(n+1)
            nodes[n].pickup_items.extend(duplicated_node.pickup_items)
            nodes[n].delivery_items.extend(duplicated_node.delivery_items)
            continue
        n += 1