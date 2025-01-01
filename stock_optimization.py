from data_model import load_warehouse_data_from_csv, save_warehouse_stock_to_csv
from datetime import datetime
import heapq
import math


def display_warehouse_stock(warehouses):
    """Display the stock status of all warehouses."""
    for warehouse_code, warehouse in warehouses.items():
        print(f"Warehouse {warehouse_code}:")
        for stock in warehouse.get_stock():
            print(f"  Item: {stock['item_code']}, Quantity: {stock['quantity']}, Min Amount: {stock['min_amount']}, Expiry Date: {stock['expiry_date']}")
    print()

def move_stock(source, destination, stock_to_move, warehouses):
    """
    Move stock from one warehouse to another.
    :param source: Source warehouse code.
    :param destination: Destination warehouse code.
    :param stock_to_move: Dictionary {item_code: quantity}.
    :param warehouses: Dictionary of warehouse objects.
    """
    source_warehouse = warehouses[source]
    dest_warehouse = warehouses[destination]
    source_stock = source_warehouse.get_stock()
    dest_stock = dest_warehouse.get_stock()
    text_output = ""

    for item_code, quantity in stock_to_move.items():
        for stock in source_stock:
            if stock['item_code'] == item_code:
                available_quantity = stock['quantity'] - stock['min_amount']
                if available_quantity >= quantity:
                    stock['quantity'] -= quantity
                else:
                    raise ValueError(f"Insufficient stock in warehouse {source} for item {item_code}.")
                break
        else:
            raise ValueError(f"Item {item_code} not found in warehouse {source}.")

        for stock in dest_stock:
            if stock['item_code'] == item_code:
                stock['quantity'] += quantity
                break
        else:
            dest_warehouse.add_stock({
                "item_code": item_code,
                "quantity": quantity,
                "min_amount": 0,
                "expiry_date": None,
            })

    print(f"Moved stock {stock_to_move} from {source} to {destination}.")
    text_output += f"Moved stock {stock_to_move} from {source} to {destination}."
    return text_output

def heuristic(stock, required_stock):
    """
    Heuristic function to calculate the penalty for insufficient stock and expiry dates.
    :param stock: List of stock dictionaries for a warehouse.
    :param required_stock: Dictionary of required stock items and their quantities.
    :return: Total penalty for insufficient stock and expiry concerns.
    """
    penalty = 0
    stock_dict = {item['item_code']: item for item in stock}
    
    for item_code, required_amount in required_stock.items():
        item = stock_dict.get(item_code)
        if item:
            available_amount = item['quantity'] - item['min_amount']
            if available_amount < required_amount:
                penalty += (required_amount - available_amount) * 2  # Penalty for insufficient stock

            # Reward for expiring item
            expiry_date = item.get('expiry_date')
            if expiry_date:
                expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d")
                days_to_expiry = (expiry_date - datetime.now()).days
                if days_to_expiry < 30:  # Add a penalty if expiry is within 30 days
                    penalty -= math.ceil((30 - days_to_expiry) * 0.1)  # Weight for expiry proximity
        else:
            penalty += required_amount * 2  # Penalty for completely missing stock
    
    return penalty

def find_best_warehouse(start, warehouses, required_stock):
    """
    Find the best warehouse to supply the required stock.
    :param start: Starting warehouse code.
    :param warehouses: Dictionary of warehouse objects.
    :param required_stock: Dictionary of required stock items and their quantities.
    :param db: Database instance.
    :return: Tuple (total_cost, path) or None if no suitable warehouse is found.
    """
    pq = []  # Priority queue: (total_cost, current_warehouse_code, path)
    heapq.heappush(pq, (0, start, []))
    visited = set()
    
    while pq:
        total_cost, current, path = heapq.heappop(pq)
        if current == start:
            visited.add(current)
            for neighbor, travel_cost in warehouses[current].adjacent.items():
                if neighbor not in visited:
                    g = total_cost + travel_cost
                    h = heuristic(warehouses[neighbor].get_stock(), required_stock)
                    f = g + h
                    heapq.heappush(pq, (f, neighbor, path + [current]))
        
        if current in visited:
            continue
        visited.add(current)
        
        # Check if the current warehouse can fulfill the required stock
        current_stock = warehouses[current].get_stock()
        if all(
            sum(item['quantity'] - item['min_amount'] for item in current_stock if item['item_code'] == item_code) 
            >= required_stock[item_code] for item_code in required_stock
        ):
            return total_cost, path + [current]
        
        # Explore neighbors
        for neighbor, travel_cost in warehouses[current].adjacent.items():
            if neighbor not in visited:
                g = total_cost + travel_cost
                h = heuristic(warehouses[neighbor].get_stock(), required_stock)
                f = g + h
                heapq.heappush(pq, (f, neighbor, path + [current]))
    
    return None  # No valid warehouse found

def process_required_stock(start, warehouses, required_stock):
    """
    Process required stock items as a whole first, if not fulfilled, then process items one by one.
    """
    output_text = ""
    remaining_stock = required_stock.copy()
    result = find_best_warehouse(start, warehouses, required_stock)

    if result:
        cost, path = result
        print(f"Best path: {' <- '.join(path)} with heuristic cost: {cost}")
        output_text += f"Best path: {' <- '.join(path)} with heuristic cost: {cost}\n"
        output_text += move_stock(path[-1], start, required_stock, warehouses) + "\n"
    else:
        print("No single warehouse found that can provide all the required stocks, proceed to process per item.")
        output_text += "No single warehouse found that can provide all the required stocks, proceed to process per item."
        for item_code, quantity in required_stock.items():
            print(f"\nProcessing item: {item_code}, Required Quantity: {quantity}")
            result = find_best_warehouse(start, warehouses, {item_code: quantity})
            
            if result:
                cost, path = result
                print(f"Item {item_code}: Best path: {' <- '.join(path)} with heuristic cost: {cost}")
                output_text += f"Item {item_code}: Best path: {' <- '.join(path)} with heuristic cost: {cost}\n"
                output_text += move_stock(path[-1], start, {item_code: quantity}, warehouses) + "\n"
                remaining_stock[item_code] = 0
            else:
                print(f"Unable to fulfill the quantity ({quantity}) for item {item_code}.")
                output_text += f"Unable to fulfill the quantity ({quantity}) for item {item_code}.\n"

        for item_code, quantity in remaining_stock.items():
            if quantity > 0:
                print("\nRemaining unmet stock requirements:")
                print(f"  Item: {item_code}, Remaining Quantity: {quantity}")
    return output_text

def trigger_stock_optimization(target_warehouse, required_stock):
    stock_file = "warehouse_stock.csv"
    connection_file = "warehouse_mapping.csv"
    output_stock_file = "optimized_warehouse_stock.csv"

    # Load data from CSV files into object
    warehouses = load_warehouse_data_from_csv(stock_file, connection_file)

    print("\nBefore stock movement:")
    display_warehouse_stock(warehouses)
    print(f"Target warehouse = {target_warehouse}, required stock = {required_stock}")

    output_text = process_required_stock(target_warehouse, warehouses, required_stock)

    print("\nAfter stock movement:")
    display_warehouse_stock(warehouses)
    
    save_warehouse_stock_to_csv(warehouses, output_stock_file)
    print(f"\nUpdated stock information has been saved to {output_stock_file}.")
    
    return output_text


# Stock movement simulation =================================================================
target_warehouse = "C"
required_stock = {"N007": 70, "H014": 40}
trigger_stock_optimization(target_warehouse, required_stock)
