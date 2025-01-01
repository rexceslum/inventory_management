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

def release_stock_to_customer(warehouse_code, stock_to_release, warehouses):
    """
    Release stock from a warehouse to fulfill customer requirements.
    :param warehouse_code: Warehouse code to release stock from.
    :param stock_to_release: Dictionary {item_code: quantity} to be released.
    :param warehouses: Dictionary of warehouse objects.
    """
    warehouse = warehouses[warehouse_code]
    stock = warehouse.get_stock()
    output_text = ""

    for item_code, quantity in stock_to_release.items():
        for stock_item in stock:
            if stock_item['item_code'] == item_code:
                available_quantity = stock_item['quantity'] - stock_item['min_amount']
                if available_quantity >= quantity:
                    stock_item['quantity'] -= quantity
                    print(f"Released {quantity} of {item_code} from Warehouse {warehouse_code}.")
                    output_text += f"Released {quantity} of {item_code} from Warehouse {warehouse_code}.\n"
                else:
                    raise ValueError(f"Insufficient stock in Warehouse {warehouse_code} for item {item_code}.")
                break
        else:
            raise ValueError(f"Item {item_code} not found in Warehouse {warehouse_code}.")
    return output_text


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
        output_text += release_stock_to_customer(path[-1], required_stock, warehouses) + "\n"
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
                output_text += release_stock_to_customer(path[-1], {item_code: quantity}, warehouses) + "\n"
                remaining_stock[item_code] = 0
            else:
                print(f"Unable to fulfill the quantity ({quantity}) for item {item_code}.")
                output_text += f"Unable to fulfill the quantity ({quantity}) for item {item_code}.\n"

        for item_code, quantity in remaining_stock.items():
            if quantity > 0:
                print("\nRemaining unmet stock requirements:")
                print(f"  Item: {item_code}, Remaining Quantity: {quantity}")
    return output_text

def trigger_stock_dispatch(target_warehouse, required_stock):
    stock_file = "warehouse_stock.csv"
    connection_file = "warehouse_mapping.csv"
    output_stock_file = "dispatched_warehouse_stock.csv"

    # Load data from CSV files into object
    warehouses = load_warehouse_data_from_csv(stock_file, connection_file)

    print("\nBefore stock dispatch:")
    display_warehouse_stock(warehouses)
    print(f"Target warehouse = {target_warehouse}, required stock = {required_stock}")

    output_text = process_required_stock(target_warehouse, warehouses, required_stock)

    print("\nAfter stock dispatch:")
    display_warehouse_stock(warehouses)
    
    save_warehouse_stock_to_csv(warehouses, output_stock_file)
    print(f"\nUpdated stock information has been saved to {output_stock_file}.")
    
    return output_text


# Stock movement simulation =================================================================
target_warehouse = "C"
required_stock = {"N007": 70, "H014": 40}
trigger_stock_dispatch(target_warehouse, required_stock)
