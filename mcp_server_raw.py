from fastmcp import FastMCP
from northwind_api import (
    get_customers,
    get_orders,
    get_order_details,
    get_products,
    get_shippers,
    get_employees,
)

mcp = FastMCP("northwind-raw")


@mcp.tool()
def raw_get_customers(country: str = None) -> list:
    """Get customers, optionally filtered by country."""
    return get_customers(country=country)


@mcp.tool()
def raw_get_orders(customer_id: str = None, ship_via: int = None) -> list:
    """Get orders, optionally filtered by customer or shipper."""
    return get_orders(customer_id=customer_id, ship_via=ship_via)


@mcp.tool()
def raw_get_order_details(order_id: int) -> list:
    """Get the line items for a specific order."""
    return get_order_details(order_id=order_id)


@mcp.tool()
def raw_get_products(category_id: int = None) -> list:
    """Get products, optionally filtered by category."""
    return get_products(category_id=category_id)


@mcp.tool()
def raw_get_shippers() -> list:
    """Get all shippers."""
    return get_shippers()


@mcp.tool()
def raw_get_employees() -> list:
    """Get all employees."""
    return get_employees()


if __name__ == "__main__":
    mcp.run()
