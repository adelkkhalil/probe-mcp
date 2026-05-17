from fastmcp import FastMCP
from northwind_api import (
    get_customers,
    get_orders,
    get_order_details,
    get_products,
    get_shippers,
    get_employees,
)

mcp = FastMCP("northwind-semantic")


@mcp.tool()
def customers_by_country(country: str = None) -> list:
    """Retrieve customers from the Northwind database.

    Use this tool when you need to look up customer information such as
    contact names, addresses, or business details. If *country* is provided,
    results are filtered to that country (e.g., 'USA', 'UK'). Omit *country*
    to return all customers. Valid country values include any value present in
    the Customers.Country column — call this without a filter first if unsure.
    """
    return get_customers(country=country)


@mcp.tool()
def orders(customer_id: str = None, ship_via: int = None, limit: int = 50) -> list:
    """Retrieve orders from the Northwind database.

    Use this tool when you need to inspect order history, check shipping status,
    or analyze freight costs.

    Parameters:
        customer_id: Filter by a specific CustomerID (e.g., 'ALFKI'). Omit for all orders.
        ship_via: Filter by shipper company ID. This is an integer — 1 = Speedy Express,
            2 = United Package, 3 = Federal Shipping. Always call get_shippers() first to
            look up the correct value rather than guessing.
        limit: Maximum number of rows to return (default 50, max 200). Use a smaller value
            for quick previews and increase when you need more data.

    Notes:
        - ShippedDate being NULL means the order has not shipped yet.
        - Freight is in USD.
    """
    results = get_orders(customer_id=customer_id, ship_via=ship_via)
    return results[:max(1, min(limit, 200))]


@mcp.tool()
def order_line_items(order_id: int) -> list:
    """Retrieve the line items (products and quantities) for a specific order.

    Use this tool when you need to know what products were included in an order,
    including unit price, quantity, and discount. Requires *order_id* — obtain it
    from orders() first.
    """
    return get_order_details(order_id=order_id)


@mcp.tool()
def products_by_category(category_id: int = None) -> list:
    """Retrieve products from the Northwind database.

    Use this tool when you need product information such as name, unit price,
    stock level, or supplier details. If *category_id* is provided, results are
    filtered to that category (e.g., 1 = Beverages). Omit *category_id* to return
    all products. Valid category IDs correspond to the Categories table — call this
    without a filter first if unsure.
    """
    return get_products(category_id=category_id)


@mcp.tool()
def shippers() -> list:
    """Retrieve all shipping companies used by Northwind.

    Use this tool to look up shipper IDs and company names (e.g., Speedy Express,
    United Package, Federal Shipping). Call this before orders() when you want to
    filter by *ship_via* — the parameter expects an integer ID from this list.
    """
    return get_shippers()


@mcp.tool()
def employees() -> list:
    """Retrieve all employees in the Northwind organization.

    Use this tool when you need employee information such as names, titles, or
    contact details. Returns all employees — no filtering available.
    """
    return get_employees()


@mcp.tool()
def order_with_details(order_id: int) -> dict:
    """Fetch an order header together with its line items in a single call.

    This is more efficient than calling orders() and order_line_items() separately,
    as it combines the order metadata (CustomerID, OrderDate, ShippedDate, Freight, etc.)
    with the nested list of products in that order.

    Parameters:
        order_id: The ID of the order to retrieve. Obtain from orders() first.

    Returns:
        A single dict containing all order header fields plus a 'line_items' key
        whose value is a list of dicts for each product in the order (with unit price,
        quantity, and discount). ShippedDate being NULL means the order has not shipped yet.
        Freight is in USD.
    """
    order_rows = get_orders(order_id=order_id)
    if not order_rows:
        return {"error": f"Order {order_id} not found"}
    line_items = get_order_details(order_id=order_id)
    result = order_rows[0]
    result["line_items"] = line_items
    return result


if __name__ == "__main__":
    mcp.run()
