from typing import Dict
from localsearch_structs import *

import sys, os
sys.path.append( os.path.dirname( os.path.dirname( os.path.realpath(__file__) ) ) )

from src.common.factory import Factory
from src.common.node import Node


def init_problem_data( factory_num=10, vehicle_num=10):
    factories = factory_num # alert: above 10 sorting is tricky
    vehicles  = vehicle_num # alert: above 10 sorting is tricky
    id_to_factory:Dict[str, Factory] = { f'f{i}':Factory(f'f{i}', 0, 0, 6) for i in range(factories) }
    dist_mtx = [ [ i + j if i != j else 0 for j in range (factories)] for i in range(factories) ]
    route_info:Dict[str, list] = { 'distance': dist_mtx, 'time':dist_mtx }
    id_to_unallocated_order_item:Dict[str, OrderItem] = {}
    id_to_vehicle:Dict[str, Vehicle] = { f'v{i}':Vehicle(f'v{i}', 15, i, 24) for i in range(vehicles) }
    pdata = ProblemData(id_to_factory, route_info, id_to_unallocated_order_item, id_to_vehicle)
    return pdata, id_to_vehicle


# creating initial data
pdata, id_to_vehicle = init_problem_data( factory_num=10, vehicle_num=10)
solution = LLSolution( pdata )


'''
Tests for *LLSolution.calculate_vehicle_arrival_departure()*
'''

# scenario 1: -> P -> D
v1 = id_to_vehicle['v1']
i1 = OrderItem( "i1", "", 'o1', 1, "f1", "f2", 0, 0, loading_time=10, unloading_time=10)
n1 = Node( "f1", 0, 0, pickup_item_list=[i1], delivery_item_list=[], arrive_time=10000, leave_time=11810 )
v1.destination = n1

pnode1 = LLNode('p', 1, [i1])
dnode1 = LLNode('d', 2, [i1])
solution.routes[1].insert_node_back(pnode1)
solution.routes[1].insert_node_back(dnode1)

solution.calculate_vehicle_arrival_departure(v1)
for node in solution.routes[1].factory_nodes:
    assert node.factory != 1 or node.arrival_time   == 10000, f'arrival time at factory   {1} should be {10000}, but is {node.arrival_time}'
    assert node.factory != 1 or node.departure_time == 11810, f'departure time at factory {1} should be {11810}, but is {node.departure_time}'
    assert node.factory != 2 or node.arrival_time   == 11813, f'arrival time at factory   {2} should be {11813}, but is {node.arrival_time}'
    assert node.factory != 2 or node.departure_time == 13623, f'departure time at factory {2} should be {13623}, but is {node.departure_time}'

# scenario 2: current -> P -> D, vehicle has destination by input
v2 = id_to_vehicle['v2']
v2.cur_factory_id = 'f1'
v2.leave_time_at_current_factory = 10000
i2 = OrderItem( "i2", "", 'o2', 1, "f3", "f4", 0, 0, loading_time=10, unloading_time=10)
n2 = Node( "f3", 0, 0, pickup_item_list=[i2], delivery_item_list=[], arrive_time=10002, leave_time=11812 )
v2.destination = n2

pnode2 = LLNode('p', 3, [i2])
dnode2 = LLNode('d', 4, [i2])
solution.routes[2].insert_node_back(pnode2)
solution.routes[2].insert_node_back(dnode2)

solution.calculate_vehicle_arrival_departure(v2)
for node in solution.routes[2].factory_nodes:
    assert node.factory != 3 or node.arrival_time   == 10002, f'  arrival time at factory {3} should be {10002}, but is {node.arrival_time}'
    assert node.factory != 3 or node.departure_time == 11812, f'departure time at factory {3} should be {11812}, but is {node.departure_time}'
    assert node.factory != 4 or node.arrival_time   == 11819, f'  arrival time at factory {4} should be {11819}, but is {node.arrival_time}'
    assert node.factory != 4 or node.departure_time == 13629, f'departure time at factory {4} should be {13629}, but is {node.departure_time}'

# scenario 3: current -> P -> D, vehicle has no destination by input
v3 = id_to_vehicle['v3']
v3.cur_factory_id = 'f1'
v3.leave_time_at_current_factory = 10000
i3 = OrderItem( "i3", "", 'o3', 1, "f3", "f4", 0, 0, loading_time=10, unloading_time=10)

pnode3 = LLNode('p', 3, [i3])
dnode3 = LLNode('d', 4, [i3])
solution.routes[3].insert_node_back(pnode3)
solution.routes[3].insert_node_back(dnode3)

solution.calculate_vehicle_arrival_departure(v3)
for node in solution.routes[3].factory_nodes:
    assert node.factory != 3 or node.arrival_time   == 10004, f'  arrival time at factory {3} should be {10004}, but is {node.arrival_time}'
    assert node.factory != 3 or node.departure_time == 11814, f'departure time at factory {3} should be {11814}, but is {node.departure_time}'
    assert node.factory != 4 or node.arrival_time   == 11821, f'  arrival time at factory {4} should be {11821}, but is {node.arrival_time}'
    assert node.factory != 4 or node.departure_time == 13631, f'departure time at factory {4} should be {13631}, but is {node.departure_time}'

# scenario 4: current -> P1 -> D1 = P2 -> D2, vehicle has no destination by input
v4 = id_to_vehicle['v4']
v4.cur_factory_id = 'f0'
v4.leave_time_at_current_factory = 10000
i4 = OrderItem("i4", "", 'o4', 1, "f5", "f6", 0, 0, loading_time=10, unloading_time=10)
i5 = OrderItem("i5", "", 'o5', 2, "f6", "f7", 0, 0, loading_time=20, unloading_time=20)

pnode4 = LLNode('p', 5, [i4])
dnode4 = LLNode('d', 6, [i4])
solution.routes[4].insert_node_back(pnode4)
solution.routes[4].insert_node_back(dnode4)
pnode5 = LLNode('p', 6, [i5])
dnode5 = LLNode('d', 7, [i5])
solution.routes[4].insert_node_back(pnode5)
solution.routes[4].insert_node_back(dnode5)

solution.calculate_vehicle_arrival_departure(v4)
for node in solution.routes[4].factory_nodes:
    assert  node.factory != 5                          or node.arrival_time   == 10005, f'  arrival time at factory {5} should be {10005}, but is {node.arrival_time}'
    assert  node.factory != 5                          or node.departure_time == 11815, f'departure time at factory {5} should be {11815}, but is {node.departure_time}'
    assert (node.factory != 6 or not node.is_delivery) or node.arrival_time   == 11826, f'  arrival time at factory {6} should be {11826}, but is {node.arrival_time}'
    assert (node.factory != 6 or not node.is_delivery) or node.departure_time == 13636, f'departure time at factory {6} should be {13636}, but is {node.departure_time}'
    assert (node.factory != 6 or not node.is_pickup)   or node.arrival_time   == 13636, f'  arrival time at factory {6} should be {13636}, but is {node.arrival_time}'
    assert (node.factory != 6 or not node.is_pickup)   or node.departure_time == 13656, f'departure time at factory {6} should be {13656}, but is {node.departure_time}'
    assert  node.factory != 7                          or node.arrival_time   == 13669, f'  arrival time at factory {7} should be {13669}, but is {node.arrival_time}'
    assert  node.factory != 7                          or node.departure_time == 15489, f'departure time at factory {7} should be {15489}, but is {node.departure_time}'


'''
Tests for *LLSolution.check_destination_constraint()*
'''

# scenario 1: -> P -> D
assert solution.check_destination_constraint(v1), f'destination constraint should be satisfied'
solution.routes[1].remove_node( pnode1 )
solution.routes[1].insert_node_back( pnode1 )
assert not solution.check_destination_constraint(v1), f'destination constraint should be violated'
solution.routes[1].remove_node( dnode1 )
solution.routes[1].insert_node_back( dnode1 )
assert solution.check_destination_constraint(v1), f'destination constraint should be satisfied'

'''
Tests for *LLSolution.check_capacity_constraint()*
'''

# scenario 5: current -> P1 -> P2 -> D2 -> D1
v5 = id_to_vehicle['v5']
i6 = OrderItem("i6", "", 'o6', 8, "f5", "f6", 0, 0, loading_time=10, unloading_time=10)
i7 = OrderItem("i7", "", 'o7', 7, "f7", "f8", 0, 0, loading_time=20, unloading_time=20)

pnode6 = LLNode('p', 5, [i6])
dnode6 = LLNode('d', 6, [i6])
pnode7 = LLNode('p', 7, [i7])
dnode7 = LLNode('d', 8, [i7])
solution.routes[5].insert_node_back(pnode6)
solution.routes[5].insert_node_back(pnode7)
solution.routes[5].insert_node_back(dnode7)
solution.routes[5].insert_node_back(dnode6)

assert solution.check_capacity_constraint(v5), f'capacity constraint should be satisfied'
v5.carrying_items.items.append(i1)
assert not solution.check_capacity_constraint(v5), f'capacity constraint should be violated'
v5.carrying_items.items.pop()
assert solution.check_capacity_constraint(v5), f'capacity constraint should be satisfied'

'''
Tests for *LLSolution.check_LIFO_constraint()*
'''

# scenario 5: current -> P1 -> P2 -> D2 -> D1
assert solution.check_LIFO_constraint(v5), f'LIFO constraint should be satisfied'
solution.routes[5].remove_node( dnode7 )
solution.routes[5].insert_node_back( node_to_insert=dnode7 )
assert not solution.check_LIFO_constraint(v5), f'LIFO constraint should be satisfied'
solution.routes[5].remove_node( dnode7 )
solution.routes[5].insert_node_after( node_to_insert=dnode7, after=pnode7 )
assert solution.check_LIFO_constraint(v5), f'LIFO constraint should be satisfied'


'''
Tests for *LLSolution.check_all_route_constraints()*
'''

# checking feasibility of all routes above and testing the violation of each route constraint
assert solution.check_all_route_constraints(), f'solution should be feasible'

solution.routes[1].remove_node( pnode1 )
solution.routes[1].insert_node_back( pnode1 )
assert not solution.check_all_route_constraints(), f'solution should not be feasible'
solution.routes[1].remove_node( dnode1 )
solution.routes[1].insert_node_back( dnode1 )
assert solution.check_all_route_constraints(), f'solution should be feasible'

v5.carrying_items.items.append(i1)
assert not solution.check_all_route_constraints(), f'solution should not be feasible'
v5.carrying_items.items.pop()
assert solution.check_all_route_constraints(), f'solution should be feasible'

solution.routes[5].remove_node( dnode7 )
solution.routes[5].insert_node_back( node_to_insert=dnode7 )
assert not solution.check_all_route_constraints(), f'solution should not be feasible'
solution.routes[5].remove_node( dnode7 )
solution.routes[5].insert_node_after( node_to_insert=dnode7, after=pnode7 )
assert solution.check_all_route_constraints(), f'solution should be feasible'


'''
Tests for *LLSolution.evaluate()*
'''

# creating new initial data
pdata, id_to_vehicle = init_problem_data( factory_num=10, vehicle_num=3 )
solution = LLSolution( pdata )

i11 = OrderItem("i11", "", 'o1', 7, "f1", "f9", 0, committed_completion_time=11830, loading_time=10, unloading_time=10) # will arrive at 11830 - not tardy
i12 = OrderItem("i12", "", 'o1', 7, "f1", "f9", 0, committed_completion_time=11830, loading_time=10, unloading_time=10) # will arrive at 11830 - not tardy
i21 = OrderItem("i21", "", 'o2', 7, "f2", "f8", 0, committed_completion_time=15000, loading_time=20, unloading_time=20) # will arrive at 15511 - tardy: 511
i22 = OrderItem("i22", "", 'o2', 7, "f2", "f8", 0, committed_completion_time=15000, loading_time=20, unloading_time=20) # will arrive at 15511 - tardy: 511
i31 = OrderItem("i31", "", 'o3', 8, "f3", "f7", 0, committed_completion_time=12000, loading_time=30, unloading_time=30) # will arrive at 11843 - not tardy
i32 = OrderItem("i32", "", 'o3', 8, "f3", "f7", 0, committed_completion_time=12000, loading_time=30, unloading_time=30) # will arrive at 15523 - tardy: 3523

# vehicle 1: -> P (f1) -> D (f9) -> P (f2) -> P (f8), f1 is the destination for v1
# taking o1 (will be in time) and o2 (will be tardy)
v1 = id_to_vehicle['v1']
v1_dest = Node( "f1", 0, 0, pickup_item_list=[i11, i12], delivery_item_list=[], arrive_time=10000, leave_time=11820 )
v1.destination = v1_dest
pnode_o1 = LLNode('p', 1, [i11, i12])
dnode_o1 = LLNode('d', 9, [i11, i12])
pnode_o2 = LLNode('p', 2, [i21, i22])
dnode_o2 = LLNode('d', 8, [i21, i22])
solution.routes[1].insert_node_back(pnode_o1)
solution.routes[1].insert_node_back(dnode_o1)
solution.routes[1].insert_node_back(pnode_o2)
solution.routes[1].insert_node_back(dnode_o2)

# vehicle 2: current (f0) -> P (f1) -> D (f9) -> P (f2) -> P (f8), f1 is the destination for v1
# taking o3 (will be tardy, because though i31 will be in time, i32 will be tardy)
v2 = id_to_vehicle['v2']
v2.cur_factory_id = 'f0'
v2.leave_time_at_current_factory = 10000
pnode_i31 = LLNode('p', 3, [i31])
dnode_i31 = LLNode('d', 7, [i31])
pnode_i32 = LLNode('p', 3, [i32])
dnode_i32 = LLNode('d', 7, [i32])
solution.routes[2].insert_node_back(pnode_i31)
solution.routes[2].insert_node_back(dnode_i31)
solution.routes[2].insert_node_back(pnode_i32)
solution.routes[2].insert_node_back(dnode_i32)

# tests for distance, tardiness and score
v1_dist = solution.vehicle_distance( v1 )
v2_dist = solution.vehicle_distance( v2 )
assert v1_dist == 31, f'distance for vehicle {1} should be {31}, but is {v1_dist}'
assert v2_dist == 33, f'distance for vehicle {2} should be {33}, but is {v2_dist}'

order_id_to_tardiness = solution.calculate_tardiness_dict()
assert order_id_to_tardiness['o1'] == 0, f'tardiness of order {"o1"} should be {0}, but is {order_id_to_tardiness["o1"]}'
assert order_id_to_tardiness['o2'] == 511, f'tardiness of order {"o2"} should be {511}, but is {order_id_to_tardiness["o2"]}'
assert order_id_to_tardiness['o3'] == 3523, f'tardiness of order {"o3"} should be {3523}, but is {order_id_to_tardiness["o3"]}'

score = solution.evaluate()
assert round( score, 2 ) == 11226.89, f'score should be {11226.89}, but is { round( score, 2 ) }'


'''
Tests for *LLNode.following_factory_nodes()*
'''
# creating test route with nodes begin -> 0 -> 1 -> ... -> 9 -> end 
test_route = LLRoute()
for i in range(10):
    nodetype = 'p' if i % 2 == 0 else 'd'
    new_node = LLNode(nodetype, i)
    test_route.insert_node_back(new_node)
# select node 5
selected_node = test_route.first
while selected_node.factory < 5:
    selected_node = selected_node.succ
# test
for idx, node in enumerate(selected_node.following_factory_nodes):
    if idx == 0:
        assert node.factory == 5,   f"first node should be no. 5"
    if idx == 4:
        assert node.factory == 9,   f"last node should be no. 9"
    assert idx + 5 == node.factory, f"factory number does not match"
    assert idx <= 4,                f"idx should not exceed 4"


'''
Feedback
'''

# if no AssertionError
print( "SUCCESS" )