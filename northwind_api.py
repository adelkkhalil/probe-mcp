import sqlite3

DB = "northwind.db"


def _query(sql, params=()):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_customers(country=None):
    if country:
        return _query(
            "SELECT * FROM Customers WHERE Country = ?",
            (country,)
        )
    return _query("SELECT * FROM Customers")


def get_orders(customer_id=None, ship_via=None, order_id=None):
    where, params = [], []
    if customer_id:
        where.append("CustomerID = ?")
        params.append(customer_id)
    if ship_via:
        where.append("ShipVia = ?")
        params.append(ship_via)
    if order_id:
        where.append("OrderID = ?")
        params.append(order_id)
    sql = "SELECT * FROM Orders"
    if where:
        sql += " WHERE " + " AND ".join(where)
    return _query(sql, tuple(params))


def get_order_details(order_id):
    return _query(
        "SELECT * FROM [Order Details] WHERE OrderID = ?",
        (order_id,)
    )


def get_products(category_id=None):
    if category_id:
        return _query(
            "SELECT * FROM Products WHERE CategoryID = ?",
            (category_id,)
        )
    return _query("SELECT * FROM Products")


def get_shippers():
    return _query("SELECT * FROM Shippers")

def get_employees():
    return _query(
        "SELECT EmployeeID, LastName, FirstName, Title, TitleOfCourtesy, "
        "BirthDate, HireDate, Address, City, Region, PostalCode, Country, "
        "HomePhone, Extension, Notes, ReportsTo FROM Employees"
    )
