from __future__ import annotations
from typing import Generator, List, Dict

import sys, os
sys.path.append( os.path.dirname( os.path.dirname( os.path.realpath(__file__) ) ) )

from src.conf.configs import Configs
from src.common.order import OrderItem
from src.common.vehicle import Vehicle
from algorithm.problemdata import ProblemData
from algorithm.priority_queue import PriorityQueue

class LLNode:
    """
    Simple class for nodes.
    """
    def __init__( self, nodetype:str, factory:int = None, items:List[OrderItem] = None, partner:LLNode = None ):
        assert nodetype in {'begin', 'end', 'p', 'd'}, f'"{nodetype}" is not a valid node type'
        if nodetype in {'begin', 'end'}:
            assert factory == None, f'no factory belongs to a "{nodetype}" node'
            assert items == None, f'no item list belongs to a "{nodetype}" node'
        if nodetype in {'p', 'd'}:
            assert type(factory) == int, f'"{factory}" is not a valid factory number, because it is a {type(factory)} object'
            assert factory >= 0, f'"{factory}" is not a valid factory number'

        self.nodetype:str = nodetype
        self.factory:int  = factory
        self.pred:LLNode  = None            # predecessor node
        self.succ:LLNode  = None            # successor node
        self.items:List[OrderItem] = items
        self.arrival_time:int   = None
        self.departure_time:int = None
        self.partner = partner
        
    def __str__( self ) -> str:
        if self.nodetype in {'p', 'd'}:
            return f'{self.factory}'
        else:
            return f'{self.nodetype}' # begin or end
    
    def remove( self ) -> None:
        """
        Removes node from its current position.
        """
        assert self.pred != None, f'could not remove node "{self}" without predecessor'
        assert self.succ != None, f'could not remove node "{self}" without successor'

        self.pred.succ = self.succ
        self.succ.pred = self.pred
        self.pred = None
        self.succ = None

    def insert_after( self, after:LLNode ) -> None:
        """
        Inserts node after the given node.

        Parameters:
            - after: the node to insert after
        """
        assert self.pred == None,  f'could not insert node "{self}" with existing predecessor ({self.pred})'
        assert self.succ == None,  f'could not insert node "{self}" with existing successor ({self.succ})'
        assert after.succ != None, f'could not insert node "{self}" after node "{after}" without successor'

        self.succ = after.succ
        self.pred = after
        after.succ.pred = self
        after.succ = self

    @property
    def is_pickup( self ) -> bool:
        """
        Returns whether the node is a pickup node or not.
        """
        return self.nodetype == 'p'
    
    @property
    def is_delivery( self ) -> bool:
        """
        Returns whether the node is a delivery node or not.
        """
        return self.nodetype == 'd'
    
    @property
    def is_factory( self ) -> bool:
        """
        Returns whether the node is a factory node or not.
        """
        return self.is_pickup or self.is_delivery
    
    @property
    def pred_has_factory( self ) -> bool:
        """
        Returns whether predecessor node is a factory node or not.
        """
        return self.pred and self.pred.is_factory
    
    @property
    def loading_time( self ) -> int:
        """
        Time of loading all the items. Unit: second.
        """
        loading_time_list = [item.load_time for item in self.items]
        return sum(loading_time_list)

    @property
    def unloading_time( self ) -> int:
        """
        Time of unloading all the items. Unit: second.
        """
        unloading_time_list = [item.unload_time for item in self.items]
        return sum(unloading_time_list)

    @property
    def overall_time_no_queuing( self ) -> int:
        # used in naive algorithm
        """
        Overall time to be spent at the node without queuing time. Unit: second.
        """
        assert self.is_factory, f'"{self.nodetype}" is not a factory node'

        overall_time = Configs.DOCK_APPROACHING_TIME if not self.pred_has_factory or self.factory != self.pred.factory else 0
        overall_time += self.loading_time if self.is_pickup else self.unloading_time

        return overall_time
    
    @property
    def following_factory_nodes( self ) -> Generator[LLNode,None,None]:
        """
        Generator function for all factory nodes in the successor string.
        """
        if not self.succ:
            return
        
        node = self.succ
        while node.succ:
            yield node
            node = node.succ


class LLRoute:
    """
    Simple class for routes.
    """
    def __init__( self ):
        self.begin = LLNode( "begin" ) # tail
        self.end   = LLNode( "end" )   # head

        self.begin.succ = self.end
        self.end.pred = self.begin

    def insert_string_after( self, str_first:LLNode, str_last:LLNode, after:LLNode ) -> None:
        """
        Inserts the given string after the given node.

        Parameters:
            - str_first: first node of the string
            - str_last:  last node of the string
            - after:     the node to insert after
        """
        assert str_first.pred == None, f'could not insert string "{str_first} -> .. -> {str_last}" into route "{self}"'
        assert str_last.succ == None,  f'could not insert string "{str_first} -> .. -> {str_last}" into route "{self}"'
        assert after.succ != None,     f'could not insert string "{str_first} -> .. -> {str_last}" into route "{self}"'

        str_last.succ = after.succ
        after.succ.pred = str_last
        str_first.pred = after
        after.succ = str_first

    def insert_node_after( self, node_to_insert:LLNode, after:LLNode ) -> None:
        """
        Inserts the given node after the given node.

        Parameters:
            - node_to_insert: the node to insert
            - after:          the node to insert after
        """
        self.insert_string_after( node_to_insert, node_to_insert, after )

    def insert_string_back( self, str_begin:LLNode, str_end:LLNode ) -> None:
        """
        Inserts the given string to the end of the route.

        Parameters:
            - str_first: first node of the string
            - str_last:  last node of the string
        """
        self.insert_string_after( str_begin, str_end, self.end.pred )

    def insert_node_back( self, node_to_insert:LLNode ) -> None:
        """
        Inserts the given node to the end of the route.

        Parameters:
            - node_to_insert: the node to insert
        """
        self.insert_string_back( node_to_insert, node_to_insert )

    def remove_string( self, str_first:LLNode, str_last:LLNode ) -> None:
        """
        Removes the given string from its current position.

        Parameters:
            - str_first: first node of the string
            - str_last:  last node of the string

        Note that string may not belongs to the route.
        """
        assert str_first.pred != None, 'could not remove string from route'
        assert str_last.succ != None, 'could not remove string from route'

        str_first.pred.succ = str_last.succ
        str_last.succ.pred = str_first.pred
        str_first.pred = None
        str_last.succ = None

    def remove_node( self, node_to_remove:LLNode ) -> None:
        """
        Removes the given node from its current position.

        Parameters:
            - node_to_remove: the node to remove

        Note that node may not belongs to the route.
        """
        self.remove_string( node_to_remove, node_to_remove )

    @property
    def empty( self ) -> bool:
        """
        Returns whether the route is empty or not.
        """
        return self.begin.succ == self.end
    
    @property
    def first( self ) -> LLNode:
        """
        Returns the first inner node of the route, if any. Returns None otherwise.        
        """
        return self.begin.succ if not self.empty else None
    
    @property
    def last( self ) -> LLNode:
        """
        Returns the last inner node of the route, if any. Returns None otherwise.        
        """
        return self.end.pred if not self.empty else None

    @property
    def factory_nodes( self ) -> Generator[LLNode,None,None]:
        """
        Generator function for inner nodes.
        """
        if self.empty:
            return
        node = self.first
        while node != self.end:
            yield node
            node = node.succ

    @property
    def nodes_except_end( self ) -> Generator[LLNode,None,None]:
        """
        Generator function for nodes, except the head.
        """
        yield self.begin
        yield from self.factory_nodes

    @property
    def nodes( self ) -> Generator[LLNode,None,None]:
        """
        Generator function for all nodes.
        """
        yield self.begin
        yield from self.factory_nodes
        yield self.end

    def __str__( self ) -> str:
        return f'route: {self.to_string()}'
    
    def to_string( self ) -> str:
        return ' -> '.join( map( str, list(self.nodes) ) )
    
    def overall_time( self, travel_time_mtx:List[list]) -> int:
        # used in naive algorithm
        """
        Overall time from the first factory node to the last factory node. Unit: second.
        Note that time to be spent at factories is also included, except queuing time.
        Note that travel time to the first factory is not included.
        """
        overall_time = 0
        for node in self.factory_nodes:
            overall_time += node.overall_time_no_queuing
            if node.succ != self.end:
                overall_time += travel_time_mtx[node.factory][node.succ.factory]
        return overall_time
    
    def last_pickup( self ) -> LLNode:
        """
        Returns last pickup node of route if any exists, otherwise returns pred of end node.
        """
        current_pickup = None
        for node in self.factory_nodes:
            if node.nodetype == 'p':
                current_pickup = node
        ret_node = current_pickup if current_pickup else self.end.pred
        return ret_node


class LLSolution:
    """
    Simple class for solutions: list of routes.
    The route with index i belongs to vehicle i.
    """
    def __init__( self, pdata:ProblemData ) -> None:
        self.__pdata:ProblemData  = pdata
        self.routes:List[LLRoute] = [ LLRoute() for vehicle in self.__pdata.vehicles] # list of routes

    def remove_string( self, str_first:LLNode, str_last:LLNode ) -> None:
        """
        Removes the given string from its current position.
        Parameters:
            - str_first: first node of the string
            - str_last:  last node of the string
        """
        assert str_first.pred != None, 'could not remove string: first node has no predecessor'
        assert str_last.succ != None, 'could not remove string: last node has no successor'

        str_first.pred.succ = str_last.succ
        str_last.succ.pred = str_first.pred
        str_first.pred = None
        str_last.succ = None

    def insert_string_after( self, str_first:LLNode, str_last:LLNode, after:LLNode ) -> None:
        """
        Inserts the given string after the given node.
        Parameters:
            - str_first: first node of the string
            - str_last:  last node of the string
            - after:     the node to insert after
        """
        assert str_first.pred == None, f'could not insert string: first node already has a predecessor'
        assert str_last.succ == None,  f'could not insert string: last node already has a successor'
        assert after.succ != None,     f'could not insert string: node to insert after has no successor'

        str_last.succ = after.succ
        after.succ.pred = str_last
        str_first.pred = after
        after.succ = str_first

    def calculate_vehicle_arrival_departure( self, vehicle:Vehicle):
        route:LLRoute = self.routes[vehicle.no]
        for node in route.factory_nodes:
            if node == route.first:
                if vehicle.destination:
                    node.arrival_time = vehicle.destination.arrive_time
                else:
                    current_factory:int  = self.__pdata.factory_id_to_int[vehicle.cur_factory_id]
                    node.arrival_time = vehicle.leave_time_at_current_factory + self.__pdata.time_mtx[current_factory][node.factory]
            else:
                node.arrival_time = node.pred.departure_time + self.__pdata.time_mtx[node.pred.factory][node.factory]
            node.departure_time = node.arrival_time + node.overall_time_no_queuing
    
    def calculate_all_arrival_departure( self ):
        for vehicle in self.__pdata.vehicles:
            self.calculate_vehicle_arrival_departure(vehicle)

    def check_destination_constraint( self, vehicle:Vehicle) -> bool:
        if vehicle.destination:
            if self.routes[vehicle.no].empty:
                return False
            dest_no = self.__pdata.factory_id_to_int[vehicle.destination.id]
            first_node_no = self.routes[vehicle.no].first.factory
            return first_node_no == dest_no
        else:
            return True

    def check_capacity_constraint( self, vehicle:Vehicle) -> bool:
        route:LLRoute = self.routes[vehicle.no]
        weight = sum( [item.demand for item in vehicle.carrying_items.items] )
        for node in route.factory_nodes:
            if node.is_pickup:
                weight += sum( [item.demand for item in node.items] )
            if node.is_delivery:
                weight -= sum( [item.demand for item in node.items] )
            if weight > vehicle.board_capacity:
                return 0
        return 1
    
    def check_LIFO_constraint( self, vehicle:Vehicle) -> bool:
        route:LLRoute = self.routes[vehicle.no]
        stack:List[OrderItem] = vehicle.carrying_items.items[:]
        for node in route.factory_nodes:
            if node.is_pickup:
                stack.extend( node.items )
            if node.is_delivery:
                for item in node.items:
                    if item.id != stack.pop().id:
                        return 0
        assert not stack, f'LIFO list is not empty at the end of route for vehicle {vehicle.no}'
        return 1
    
    def check_vehicle_route_constraints( self, vehicle:Vehicle) -> bool:
        if not self.check_destination_constraint( vehicle ):
            return 0
        if not self.check_capacity_constraint( vehicle ):
            return 0
        if not self.check_LIFO_constraint( vehicle ):
            return 0
        return 1
    
    def check_all_route_constraints( self ) -> bool:
        for vehicle in self.__pdata.vehicles:
            if not self.check_vehicle_route_constraints( vehicle ):
                return 0
        return 1
    
    def vehicle_distance( self, vehicle:Vehicle ) -> float:
        route:LLRoute = self.routes[vehicle.no]
        if route.empty:
            return 0
        distance_traveled = 0
        if vehicle.cur_factory_id:
            cur_factory_no = self.__pdata.factory_id_to_int[vehicle.cur_factory_id]
            first_node_no = route.first.factory
            distance_traveled += self.__pdata.distance( cur_factory_no, first_node_no )
        node = route.first
        while node.succ != route.end:
            distance_traveled += self.__pdata.distance( node.factory, node.succ.factory )
            node = node.succ
        
        return distance_traveled

    def total_distance( self ) -> float:
        total_distance = sum( [ self.vehicle_distance(vehicle) for vehicle in self.__pdata.vehicles ]  )
        return total_distance

    def calculate_tardiness_dict( self ) -> Dict[str, int]:
        order_id_to_tardiness:Dict[str, int] = {}
        self.calculate_all_arrival_departure()
        for route in self.routes:
            for node in route.factory_nodes:
                if not node.is_delivery:
                    continue
                for item in node.items:
                    order_id = item.order_id
                    item_tardiness = max( 0, node.arrival_time - item.committed_completion_time)
                    if order_id in order_id_to_tardiness.keys():
                        order_id_to_tardiness[order_id] = max( item_tardiness, order_id_to_tardiness[order_id] )
                    else:
                        order_id_to_tardiness[order_id] = item_tardiness

        return order_id_to_tardiness
    
    def total_tardiness( self ) -> int:
        order_id_to_tardiness = self.calculate_tardiness_dict()
        total_tardiness = sum( order_id_to_tardiness.values() )
        return total_tardiness
    
    def decorator_eval2(func):
        def wrapper(self:LLSolution):
            return self.eval2()
        return wrapper
    
    @decorator_eval2
    def evaluate( self ) -> float:
        total_distance = self.total_distance()
        vehicle_num = len(self.__pdata.vehicles)
        total_tardiness = self.total_tardiness()
        tardiness_weight = Configs.LAMDA / 3600
        score = total_distance / vehicle_num + total_tardiness * tardiness_weight
        return score
    
    def eval2( self ) -> float:
        
        # initialization
        total_dist = 0
        total_tard = 0
        order_id_to_tardiness:dict[str, int] = {}
        ARR = 'arrival'
        DEP = 'departure'
        eventq = PriorityQueue()
        factory_id_to_dockingq = { f.id:[] for f in self.__pdata.factories }

        for vehicle in self.__pdata.vehicles:
            if vehicle.cur_factory_id: # vehicle is at a factory
                dep_time = vehicle.leave_time_at_current_factory
                factory_id = vehicle.cur_factory_id
                if dep_time > vehicle.gps_update_time: # vehicle's service is in progress (waiting, docking, loading, unloading) -> add vehicle to the docking queue
                    dockingq = factory_id_to_dockingq[factory_id]
                    dockingq.append((dep_time, vehicle))
                    dockingq.sort(key=lambda tup: tup[0])
                eventq.push(dep_time, (DEP, factory_id, vehicle, self.routes[vehicle.no].begin)) # creating departure event
            else: # vehicle is traveling
                arr_time = vehicle.destination.arrive_time
                factory_id = vehicle.destination.id
                eventq.push(arr_time, (ARR, factory_id, vehicle, self.routes[vehicle.no].first)) # creating arrival event

        # processing events
        while not eventq.is_empty():
            
            event = eventq.pop()
            event_time = event.priority
            event_type = event.item[0]
            factory_id = event.item[1]
            vehicle:Vehicle = event.item[2]
            node:LLNode = event.item[3]
            
            if event_type == DEP: # departure event
                dockingq = factory_id_to_dockingq[factory_id]
                for tup in dockingq: # find vehicle in docking queue and remove
                    if tup[1] == vehicle:
                        dockingq.remove(tup)
                        break
                if node.succ.is_factory: # vehicle has a next factory to visit
                    fact_from:int = node.factory if node.nodetype != 'begin' else self.__pdata.factory_id_to_int[vehicle.cur_factory_id]
                    fact_to:int = node.succ.factory
                    arr_time = event_time + self.__pdata.time_mtx[fact_from][fact_to] # event time + travel time
                    factory_id = self.__pdata.factories[fact_to].id
                    eventq.push(arr_time, (ARR, factory_id, vehicle, node.succ)) # creating arrival event
            
            if event_type == ARR: # arrival event
                # calculate contribution to distance part of the objective
                if node == self.routes[vehicle.no].first and vehicle.cur_factory_id: # arrival is at the first factory node and we have to consider the way traveled
                    fact_from:int = self.__pdata.factory_id_to_int[vehicle.cur_factory_id]
                    fact_to:int = node.factory
                    total_dist += self.__pdata.distance(fact_from, fact_to)
                if node != self.routes[vehicle.no].first: # arrival is at a factory node distinct from the first node
                    fact_from:int = node.pred.factory
                    fact_to:int = node.factory
                    total_dist += self.__pdata.distance(fact_from, fact_to)
                # calculate contribution to tardiness part of the objective                
                while True: # loop to handle case of multiple delivery nodes at the same lociation
                    if node.is_delivery:
                        for item_to_deliver in node.items: # calculate tardiness incurring at this node
                            order_id = item_to_deliver.order_id
                            item_tardiness = max(0, event_time - item_to_deliver.committed_completion_time)
                            if order_id in order_id_to_tardiness.keys():
                                order_id_to_tardiness[order_id] = max( item_tardiness, order_id_to_tardiness[order_id] )
                            else:
                                order_id_to_tardiness[order_id] = item_tardiness
                    if node.succ.factory == node.factory:
                        node = node.succ
                    else:
                        break # at this point *node* is the last node of this location
                node:LLNode = event.item[3] # change *node* back to original
                # calculate departure time
                factory = self.__pdata.factories[node.factory]
                dock_num = factory.dock_num
                dockingq = factory_id_to_dockingq[factory_id]
                queue_size = len(dockingq)
                if dock_num > queue_size:
                    waiting_time = 0
                if dock_num <= queue_size:
                    waiting_time = dockingq[queue_size-dock_num][0] - event_time
                docking_time = Configs.DOCK_APPROACHING_TIME
                overall_loading_unloading_time = 0
                while True: # loop to handle case of multiple nodes at the same lociation
                    overall_loading_unloading_time += node.loading_time if node.is_pickup else node.unloading_time
                    if node.succ.factory == node.factory:
                        node = node.succ
                    else:
                        break # at this point *node* is the last node of this location
                dep_time = event_time + waiting_time + docking_time + overall_loading_unloading_time
                # insert vehicle into docking queue
                dockingq.append((dep_time, vehicle))
                dockingq.sort(key=lambda tup: tup[0])
                # create departure event
                eventq.push(dep_time, (DEP, factory_id, vehicle, node)) # creating departure event

        # calculate score
        vehicle_num = len(self.__pdata.vehicles)
        tard_weight = Configs.LAMDA / 3600
        total_tard = sum(order_id_to_tardiness.values())
        score = total_dist / vehicle_num + tard_weight * total_tard
        return score