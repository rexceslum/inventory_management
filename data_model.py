import csv

class Warehouse:
    def __init__(self, warehouse_code):
        self.warehouse_code = warehouse_code
        self.adjacent = {}  # Dictionary {neighbor_code: travel_cost}
        self.warehouse_stock = []  # List of stock dictionaries
    
    def add_connection(self, neighbor, cost):
        self.adjacent[neighbor] = cost
        
    def add_stock(self, stock):
        self.warehouse_stock.append(stock)

    def get_stock(self):
        return self.warehouse_stock

def load_warehouse_data_from_csv(stock_file, connection_file):
    """Load warehouse stock and connections from CSV files."""
    warehouses = {}

    # Load stock data
    with open(stock_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            warehouse_code = row['warehouse_code']
            stock = {
                "item_code": row['item_code'],
                "quantity": int(row['quantity']),
                "min_amount": int(row['min_amount']),
                "expiry_date": row['expiry_date'],
            }

            if warehouse_code not in warehouses:
                warehouses[warehouse_code] = Warehouse(warehouse_code)
            
            warehouses[warehouse_code].add_stock(stock)

    # Load connection data
    with open(connection_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            warehouse_code = row['warehouse_code']
            neighbor_code = row['neighbor_code']
            travel_cost = int(row['travel_cost'])

            if warehouse_code not in warehouses:
                warehouses[warehouse_code] = Warehouse(warehouse_code)
            if neighbor_code not in warehouses:
                warehouses[neighbor_code] = Warehouse(neighbor_code)

            warehouses[warehouse_code].add_connection(neighbor_code, travel_cost)

    return warehouses

def save_warehouse_stock_to_csv(warehouses, output_file):
    """
    Save the updated warehouse stock information to a CSV file.
    :param warehouses: Dictionary of warehouse objects.
    :param output_file: Path to the output CSV file.
    """
    with open(output_file, mode="w", newline="") as csvfile:
        fieldnames = ["warehouse_code", "item_code", "quantity", "min_amount", "expiry_date"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for warehouse_code, warehouse in warehouses.items():
            for stock in warehouse.get_stock():
                writer.writerow({
                    "warehouse_code": warehouse_code,
                    "item_code": stock["item_code"],
                    "quantity": stock["quantity"],
                    "min_amount": stock["min_amount"],
                    "expiry_date": stock["expiry_date"] if stock["expiry_date"] else "",
                })
                
