from typing import List, Dict
from src.common.factory import Factory
from src.common.order import OrderItem
from src.common.vehicle import Vehicle
import time

class ProblemData:
    def __init__( self, id_to_factory:Dict[str, Factory], route_info:Dict[str, list], id_to_unallocated_order_item:Dict[str, OrderItem], id_to_vehicle:Dict[str, Vehicle] ) -> None:

        self.creation_time:int = time.time()

        self.factories:List[Factory]          = self.create_sorted_factory_list(id_to_factory) # factory list
        self.factory_id_to_int:Dict[str, int] = self.map_factory_id_to_int(self.factories)     # map factories to integers
        
        self.distance_mtx:List[list] = route_info['distance'] # distance matrix
        self.time_mtx:List[list]     = route_info['time']     # transport time matrix

        self.unallocated_order_items:List[OrderItem] = list(id_to_unallocated_order_item.values()) # unallocated order items

        self.vehicles:List[Vehicle]           = self.create_sorted_vehicle_list(id_to_vehicle) # vehicle list
        self.vehicle_id_to_int:Dict[str, int] = self.map_vehicle_id_to_int(self.vehicles)      # map vehicles to integers

        self.current_instance:int = None
    
    def distance( self, from_node:int, to_node:int ) -> float:
        assert 0 <= from_node and from_node < len(self.factories), f'invalid factory index "{from_node}"'
        assert 0 <= to_node and to_node < len(self.factories),     f'invalid factory index "{to_node}"'

        return self.distance_mtx[from_node][to_node]
    
    def travel_time( self, from_node:int, to_node:int ) -> float:
        assert 0 <= from_node and from_node < len(self.factories), f'invalid factory index "{from_node}"'
        assert 0 <= to_node and to_node < len(self.factories),     f'invalid factory index "{to_node}"'

        return self.time_mtx[from_node][to_node]
    
    def create_sorted_factory_list( self, id_to_factory:Dict[str, Factory] ):
        factory_list = [f for f in id_to_factory.values()]
        factory_list.sort() # factories are sorted alphabetically (with respect to factory id)
        for idx, factory in enumerate(factory_list):
            factory.no = idx
        return factory_list
    
    def map_factory_id_to_int( self, factory_list:List[Factory] ):
        return { factory_list[i].id:i for i in range(len(factory_list)) }
    
    def create_sorted_vehicle_list( self, id_to_vehicle:Dict[str, Factory] ):
        vehicle_list = [v for v in id_to_vehicle.values()]
        vehicle_list.sort() # vehicles are sorted alphabetically (with respect to vehicle id)
        for idx, vehicle in enumerate(vehicle_list):
            vehicle.no = idx
        return vehicle_list
    def map_vehicle_id_to_int( self, vehicle_list:List[Vehicle] ):
        return { vehicle_list[i].id:i for i in range(len(vehicle_list)) }