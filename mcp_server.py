import sqlite3
from fastmcp import FastMCP

mcp = FastMCP("northwind-raw")
DB = "northwind.db"

def query(sql, params=()):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@mcp.tool()
def get_customers(country: str = None) -> list:
    """Get customers, optionally filtered by country."""
    if country:
        return query(
            "SELECT * FROM Customers WHERE Country = ?",
            (country,)
        )
    return query("SELECT * FROM Customers")

@mcp.tool()
def get_orders(customer_id: str = None, ship_via: int = None) -> list:
    """Get orders, optionally filtered by customer or shipper."""
    where, params = [], []
    if customer_id:
        where.append("CustomerID = ?")
        params.append(customer_id)
    if ship_via:
        where.append("ShipVia = ?")
        params.append(ship_via)
    sql = "SELECT * FROM Orders"
    if where:
        sql += " WHERE " + " AND ".join(where)
    return query(sql, tuple(params))

@mcp.tool()
def get_order_details(order_id: int) -> list:
    """Get the line items for a specific order."""
    return query(
        "SELECT * FROM [Order Details] WHERE OrderID = ?",
        (order_id,)
    )

@mcp.tool()
def get_products(category_id: int = None) -> list:
    """Get products, optionally filtered by category."""
    if category_id:
        return query(
            "SELECT * FROM Products WHERE CategoryID = ?",
            (category_id,)
        )
    return query("SELECT * FROM Products")

@mcp.tool()
def get_shippers() -> list:
    """Get all shippers."""
    return query("SELECT * FROM Shippers")

@mcp.tool()
def get_employees() -> list:
    """Get all employees."""
    return query("SELECT * FROM Employees")


if __name__ == "__main__":
    mcp.run()
