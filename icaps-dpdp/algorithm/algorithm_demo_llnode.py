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

from src.common.node import Node
from src.common.order import OrderItem
from src.conf.configs import Configs
from src.utils.input_utils import get_factory_info, read_json
from src.utils.json_tools import convert_nodes_to_json
from src.utils.json_tools import get_vehicle_instance_dict, get_order_item_dict
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

# naive (demo) dispatching method: in each iteration, the ith new order is allocated to vehicle i (modulo the number of vehicles)
def dispatch_orders_to_vehicles( problem_data:ProblemData ):
    
    # initializing solution
    vehicle_id_to_route:Dict[str, LLRoute] = { vehicle.id:LLRoute() for vehicle in problem_data.vehicles }

    # step 1
    # dealing with the carrying items of vehicles: dispatching the items according to LIFO
    # in this algorithm all the carrying items have the same delivery factory
    for vehicle in problem_data.vehicles:
        unloading_sequence_of_items:List[OrderItem] = vehicle.get_unloading_sequence()
        if not unloading_sequence_of_items:
            continue
        factory_id = unloading_sequence_of_items[0].delivery_factory_id
        factory_no = problem_data.factory_id_to_int[factory_id]
        new_node = LLNode('d', factory_no, copy.copy(unloading_sequence_of_items))
        vehicle_id_to_route[vehicle.id].insert_node_back(new_node)

    # step 2
    # dealing with the empty vehicles, that have been allocated to the order, but have not yet arrived to the pickup factory
    # the route of such a vehicle will be "pickup node" -> "delivery node"
    already_allocated_items = []
    for vehicle in problem_data.vehicles:
        if not vehicle.carrying_items.is_empty() or vehicle.destination is None:
            continue
        pickup_items:List[OrderItem] = vehicle.destination.pickup_items
        pickup_node, delivery_node = __create_pickup_and_delivery_nodes_of_items(pickup_items, problem_data.factory_id_to_int)
        vehicle_id_to_route[vehicle.id].insert_node_back(pickup_node)
        vehicle_id_to_route[vehicle.id].insert_node_back(delivery_node)
        already_allocated_items.extend([item.id for item in pickup_items])

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
    current_vehicle_idx = 0

    for order_id, items in order_id_to_items.items():
        demand = __calculate_demand(items)

        # order exceeds the capacity limit
        # partition order items to separate packages
        if demand > capacity:

            cur_demand = 0
            tmp_items = []
            for item in items:
                if cur_demand + item.demand > capacity:

                    pickup_node, delivery_node = __create_pickup_and_delivery_nodes_of_items(tmp_items, problem_data.factory_id_to_int)
                    vehicle = problem_data.vehicles[current_vehicle_idx]
                    vehicle_id_to_route[vehicle.id].insert_node_back(pickup_node)
                    vehicle_id_to_route[vehicle.id].insert_node_back(delivery_node)

                    current_vehicle_idx = (current_vehicle_idx + 1) % len(problem_data.vehicles)
                    tmp_items = []
                    cur_demand = 0

                tmp_items.append(item)
                cur_demand += item.demand

            if len(tmp_items) > 0:
                pickup_node, delivery_node = __create_pickup_and_delivery_nodes_of_items(tmp_items, problem_data.factory_id_to_int)
                vehicle = problem_data.vehicles[current_vehicle_idx]
                vehicle_id_to_route[vehicle.id].insert_node_back(pickup_node)
                vehicle_id_to_route[vehicle.id].insert_node_back(delivery_node)
        
        # order is within the capacity limit
        else:
            pickup_node, delivery_node = __create_pickup_and_delivery_nodes_of_items(items, problem_data.factory_id_to_int)
            vehicle = problem_data.vehicles[current_vehicle_idx]
            vehicle_id_to_route[vehicle.id].insert_node_back(pickup_node)
            vehicle_id_to_route[vehicle.id].insert_node_back(delivery_node)

        # move on to the next vehicle
        current_vehicle_idx = (current_vehicle_idx + 1) % len(problem_data.vehicles)

    solution = LLSolution(problem_data)
    solution.routes = [vehicle_id_to_route[vehicle.id] for vehicle in problem_data.vehicles]

    return solution


def __create_pickup_and_delivery_nodes_of_items(items: list, factory_id_to_int: dict):
    
    pickup_factory_id = __get_pickup_factory_id(items)
    delivery_factory_id = __get_delivery_factory_id(items)
    if len(pickup_factory_id) == 0 or len(delivery_factory_id) == 0:
        return None, None

    pickup_node = LLNode('p', factory_id_to_int[pickup_factory_id], copy.copy(items))
    items.reverse()
    delivery_node = LLNode('d', factory_id_to_int[delivery_factory_id], copy.copy(items))

    return pickup_node, delivery_node


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


# Combine adjacent-duplicated nodes.
def __combine_duplicated_nodes(nodes:List[Node]):
    n = 0
    while n < len(nodes)-1:
        if nodes[n].id == nodes[n+1].id:
            nodes[n].pickup_items.extend(nodes.pop(n+1).pickup_items)
        n += 1