from algorithm.problemdata           import ProblemData
from algorithm.localsearch_structs   import LLNode, LLRoute, LLSolution
from algorithm.algorithm_best_insert import find_best_insert
from src.common.vehicle              import Vehicle
import time

LS_EPSILON = 0.000001

def improve_by_couple_exchange( pdata:ProblemData, solution:LLSolution ) -> bool:
    '''
    Finds the best couple exchange, that means swapping the position of two pickup-delivery pairs (couples) in any two (or in a single) route.
    '''
    initial_value = solution.evaluate()

    best_value:float     = initial_value
    best_pickup_1:LLNode = None
    best_pickup_2:LLNode = None

    for vehicle_1 in pdata.vehicles:
        route_1:LLRoute = solution.routes[vehicle_1.no]
        for pickup_node_1 in route_1.factory_nodes:
            
            if pickup_node_1.nodetype != 'p':
                continue
            assert pickup_node_1.partner, f"pickup node without a partner node"

            # check if couple 1 is removable
            if not couple_is_removeable( solution, vehicle_1, pickup_node_1):
                continue

            following_vehicles = (f_vehicle for f_vehicle in pdata.vehicles if vehicle_1.no <= f_vehicle.no)
            for vehicle_2 in following_vehicles:
                route_2:LLRoute = solution.routes[vehicle_2.no]
                # search for a second couple
                # if in the same route, then search among the following nodes only
                gen_for_pickup_node_2 = route_2.factory_nodes if vehicle_1 != vehicle_2 else pickup_node_1.following_factory_nodes
                for pickup_node_2 in gen_for_pickup_node_2:
                    if pickup_node_2.nodetype != 'p':
                        continue
                    assert pickup_node_2.partner, f"pickup node without a partner node"

                    # check if couple 2 is removable
                    if not couple_is_removeable( solution, vehicle_2, pickup_node_2):
                        continue

                    # swap couple 1 and couple 2
                    temp1, temp2 = pickup_node_1.partner, pickup_node_2.partner
                    swap_nodes( pickup_node_1, pickup_node_2 )
                    swap_nodes( temp1, temp2 )
                    if not solution.check_vehicle_route_constraints(vehicle_1) or not solution.check_vehicle_route_constraints(vehicle_2):
                        # undo swapping (swap again)
                        temp1, temp2 = pickup_node_1.partner, pickup_node_2.partner
                        swap_nodes( pickup_node_1, pickup_node_2 )
                        swap_nodes( temp1, temp2 )
                        continue

                    # check score of new solution
                    curr_value = solution.evaluate()
                    if curr_value + LS_EPSILON < best_value:
                        best_value    = curr_value
                        best_pickup_1 = pickup_node_1
                        best_pickup_2 = pickup_node_2

                    # undo swapping (swap again)
                    temp1, temp2 = pickup_node_1.partner, pickup_node_2.partner
                    swap_nodes( pickup_node_1, pickup_node_2 )
                    swap_nodes( temp1, temp2 )
    # apply best exchange
    if best_pickup_1 != None:
        assert best_pickup_2, f"couple exchange without second couple"
        temp1, temp2 = best_pickup_1.partner, best_pickup_2.partner
        swap_nodes( best_pickup_1, best_pickup_2 )
        swap_nodes( temp1, temp2 )
        # print( f'{initial_value:.2f} -> {best_value:.2f}' )
        return True
    
    # print( f'{initial_value:.2f} -> no further improvement' )
    return False

def improve_by_block_exchange( pdata:ProblemData, solution:LLSolution ) -> bool:
    '''
    Finds the best block exchange, that means swapping the position of two strings (blocks) in any two (or in a single) route.
    '''
    initial_value = solution.evaluate()
    best_value:float         = initial_value
    best_first_node_1:LLNode = None
    best_first_node_2:LLNode = None

    for vehicle in pdata.vehicles:
        route:LLRoute = solution.routes[vehicle.no]
        for node in route.factory_nodes:
            
            if node.nodetype != 'p':
                continue
            assert node.partner, f"pickup node without a partner node"

            # remove block 1
            original_pred_1 = node.pred
            solution.remove_string( node, node.partner )
            if not solution.check_destination_constraint(vehicle):
                # undo removal of block 1
                solution.insert_string_after( node, node.partner, after=original_pred_1 )
                continue
            # find best exchange
            following_vehicles = (f_vehicle for f_vehicle in pdata.vehicles if vehicle.no <= f_vehicle.no)
            for other_vehicle in following_vehicles:
                other_route:LLRoute = solution.routes[other_vehicle.no]
                # search for a second block
                # if in the same route, then search among the following nodes only
                # it is necessary, otherwise exchange could be erroneous in case of neighboring blocks
                gen_for_other_node  = other_route.factory_nodes if vehicle != other_vehicle else original_pred_1.following_factory_nodes
                for other_node in gen_for_other_node:
                    if other_node.nodetype != 'p':
                        continue
                    assert other_node.partner, f"pickup node without a partner node"
                    # remove block 2
                    original_pred_2 = other_node.pred
                    solution.remove_string( other_node, other_node.partner )
                    if not solution.check_destination_constraint(other_vehicle):
                        # undo removal of block 2
                        solution.insert_string_after( other_node, other_node.partner, after=original_pred_2 )
                        continue
                    # try exchange
                    solution.insert_string_after( node, node.partner, after=original_pred_2 )
                    if not solution.check_vehicle_route_constraints(other_vehicle):
                        # undo insertion of block 1 and removal of block 2
                        solution.remove_string( node, node.partner )
                        solution.insert_string_after( other_node, other_node.partner, after=original_pred_2 )
                        continue
                    solution.insert_string_after( other_node, other_node.partner, after=original_pred_1 )
                    if not solution.check_vehicle_route_constraints(vehicle):
                        # undo insertion of block 2 and block 1 and removal of block 2
                        solution.remove_string( other_node, other_node.partner )
                        solution.remove_string( node, node.partner )
                        solution.insert_string_after( other_node, other_node.partner, after=original_pred_2 )
                        continue
                    curr_value = solution.evaluate()
                    if curr_value + LS_EPSILON < best_value:
                        best_value = curr_value
                        best_first_node_1 = node
                        best_first_node_2 = other_node

                    # undo insertion of block 2 and block 1 and removal of block 2
                    solution.remove_string( other_node, other_node.partner )
                    solution.remove_string( node, node.partner )
                    solution.insert_string_after( other_node, other_node.partner, after=original_pred_2 )

            # undo removal
            solution.insert_string_after( node, node.partner, after=original_pred_1 )

    # apply best exchange
    if best_first_node_1 != None:
        assert best_first_node_2, f"block exchange without second block"
        best_first_1_pred = best_first_node_1.pred
        solution.remove_string( best_first_node_1, best_first_node_1.partner )
        best_first_2_pred = best_first_node_2.pred # this must be after removing first block to avoid incorrect insertion in case of neighboring blocks
        solution.remove_string( best_first_node_2, best_first_node_2.partner )
        solution.insert_string_after( best_first_node_1, best_first_node_1.partner, after=best_first_2_pred )
        solution.insert_string_after( best_first_node_2, best_first_node_2.partner, after=best_first_1_pred )
        # print( f'{initial_value:.2f} -> {best_value:.2f}' )
        return True
    
    # print( f'{initial_value:.2f} -> no further improvement' )
    return False

def improve_by_couple_relocation( pdata:ProblemData, solution:LLSolution ) -> bool:
    '''
    Finds the best couple relocation, that means removing a pickup-delivery pair (couple) from a route and inserting it to an other position in any route.
    '''
    initial_value = solution.evaluate()

    best_value:float          = initial_value
    best_pickup_node:LLNode   = None
    best_pred_pickup:LLNode   = None
    best_pred_delivery:LLNode = None

    for vehicle in pdata.vehicles:
        route:LLRoute = solution.routes[vehicle.no]
        for pickup_node in route.factory_nodes:
            
            if pickup_node.nodetype != 'p':
                continue
            assert pickup_node.partner, f"pickup node without a partner node"

            # remove couple
            delivery_node = pickup_node.partner
            orig_pred_pickup = pickup_node.pred
            orig_pred_delivery = delivery_node.pred
            pickup_node.remove()
            delivery_node.remove()
            
            if not solution.check_vehicle_route_constraints(vehicle):
                # undo
                pickup_node.insert_after(orig_pred_pickup)
                delivery_node.insert_after(orig_pred_delivery)
                continue

            # find best insertion
            score, other_vehicle, new_pred_pickup, new_pred_delivery = find_best_insert(pdata, solution, pickup_node, delivery_node)
            if score + LS_EPSILON < best_value:
                best_value         = score
                best_pickup_node   = pickup_node
                best_pred_pickup   = new_pred_pickup
                best_pred_delivery = new_pred_delivery

            # undo removal
            pickup_node.insert_after(orig_pred_pickup)
            delivery_node.insert_after(orig_pred_delivery)

    # apply best relocation
    if best_pickup_node != None:
        best_pickup_node.remove()
        best_pickup_node.partner.remove()
        best_pickup_node.insert_after(best_pred_pickup)
        best_pickup_node.partner.insert_after(best_pred_delivery)
        # print( f'{initial_value:.2f} -> {best_value:.2f}' )
        return True
    
    # print( f'{initial_value:.2f} -> no further improvement' )
    return False

def improve_by_block_relocation( pdata:ProblemData, solution:LLSolution ) -> bool:
    '''
    Finds the best block relocation, that means removing a string (block) from a route and inserting it to an other position in any route.
    '''
    initial_value = solution.evaluate()

    best_value:float       = initial_value
    best_first_node:LLNode = None
    best_after:LLNode      = None

    for vehicle in pdata.vehicles:
        route:LLRoute = solution.routes[vehicle.no]
        for node in route.factory_nodes:
            
            if node.nodetype != 'p':
                continue
            assert node.partner, f"pickup node without a partner node"

            # remove block
            original_pred = node.pred
            solution.remove_string( node, node.partner )
            if not solution.check_vehicle_route_constraints(vehicle):
                # undo
                solution.insert_string_after( node, node.partner, after=original_pred )
                continue

            # find best insertion
            for other_vehicle in pdata.vehicles:
                other_route:LLRoute = solution.routes[other_vehicle.no]
                for after in other_route.nodes_except_end:
                    solution.insert_string_after( node, node.partner, after=after )
                    if not solution.check_vehicle_route_constraints(other_vehicle):
                        # undo insertion
                        solution.remove_string( node, node.partner )
                        continue
                    curr_value = solution.evaluate()
                    if curr_value + LS_EPSILON < best_value:
                        best_value = curr_value
                        best_first_node = node
                        best_after = after
                    # undo insertion
                    solution.remove_string( node, node.partner )

            # undo removal
            solution.insert_string_after( node, node.partner, after=original_pred )

    # apply best relocation
    if best_first_node != None:
        solution.remove_string( best_first_node, best_first_node.partner )
        solution.insert_string_after( best_first_node, best_first_node.partner, after=best_after )
        # print( f'{initial_value:.2f} -> {best_value:.2f}' )
        return True
    
    # print( f'{initial_value:.2f} -> no further improvement' )
    return False

def improve( pdata:ProblemData, solution:LLSolution ) -> None:
    if time.time() - pdata.creation_time > 9.5 * 60:
        return False
    if improve_by_block_relocation( pdata, solution ):
        return True
    if time.time() - pdata.creation_time > 9.5 * 60:
        return False
    if improve_by_couple_relocation( pdata, solution):
        return True
    if time.time() - pdata.creation_time > 9.5 * 60:
        return False
    if improve_by_block_exchange( pdata, solution):
        return True
    if time.time() - pdata.creation_time > 9.5 * 60:
        return False
    if improve_by_couple_exchange( pdata, solution):
        return True
    return False


'''
Aux functions
'''

def swap_nodes( n1:LLNode, n2:LLNode) -> None:
    assert n1.pred and n1.succ, f"could not swap node without succ and/or pred"
    assert n2.pred and n2.succ, f"could not swap node without succ and/or pred"
    # nothing to do if n1 and n2 are the same
    if n1 == n2:
        return
    # dealing with the case of neighboring nodes
    if n1.succ == n2:
        n1.remove()
        n1.insert_after(n2)
        return
    if n2.succ == n1:
        n2.remove()
        n2.insert_after(n1)
        return
    # general case
    n1_pred = n1.pred
    n1.remove()
    n1.insert_after(n2)
    n2.remove()
    n2.insert_after(n1_pred)

def remove_couple( pickup_node:LLNode ) -> None:
    assert pickup_node.nodetype == 'p', f"could not remove couple with incorrect pickup node"
    assert pickup_node.partner, f"pickup node without a partner node"
    pickup_node.remove()
    pickup_node.partner.remove()

def couple_is_removeable( solution:LLSolution, vehicle:Vehicle, pickup_node:LLNode ) -> bool:
    # remove couple
    pred_pickup = pickup_node.pred
    pred_delivery = pickup_node.partner.pred
    remove_couple(pickup_node)
    # check destination constraint (capacity and LIFO will not be violated)
    retval = solution.check_destination_constraint(vehicle)
    # undo removal of couple
    pickup_node.insert_after(pred_pickup)
    pickup_node.partner.insert_after(pred_delivery)
    
    return retval
    
    


        

