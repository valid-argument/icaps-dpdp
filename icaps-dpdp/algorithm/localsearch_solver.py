from algorithm.problemdata              import ProblemData
from algorithm.localsearch_structs      import LLSolution
from algorithm.algorithm_best_insert    import __read_input_json, __output_json
from algorithm.algorithm_best_insert    import dispatch_orders_to_vehicles, convert_solution
from algorithm.localsearch              import improve


def scheduling() -> None:
    """
    Dispatches orders.
    """
    pdata = __init_problemdata()
    solution = __create_initial_solution( pdata )
    __improve_solution( pdata, solution )
    __output_solution( pdata, solution )


def __init_problemdata() -> ProblemData:
    """
    Creates and initializes problem data.
    Returns: problem data.
    """
    pdata = __read_input_json()
    return pdata


def __create_initial_solution( pdata:ProblemData ) -> LLSolution:
    """
    Creates initial solution.
    Returns: initial solution.
    """
    solution = dispatch_orders_to_vehicles( pdata )
    return solution


def __improve_solution( pdata:ProblemData, solution:LLSolution ) -> None:
    """
    Improves the given solution.
    """
    while improve(pdata, solution):
        continue


def __output_solution( pdata:ProblemData, solution:LLSolution ) -> None:
    """Writes the necessary output files according to the given solution."""
    vehicle_id_to_destination, vehicle_id_to_planned_route = convert_solution(pdata, solution)
    __output_json(vehicle_id_to_destination, vehicle_id_to_planned_route)