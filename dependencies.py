import psycopg2
import pandas as pd

def get_db_connection():
    try:
        connection = psycopg2.connect(
            host="host",
            database="database",
            user="user",
            password="password")
        return connection
    except psycopg2.Error as e:
        print(f"Error: {e}")
        return None
    

def fetch_users():
    connection = get_db_connection()
    if connection is not None:
        try:
            cursor = connection.cursor()
            cursor.execute('SELECT * FROM admin')
            # Fetch column names
            columns = [desc[0] for desc in cursor.description]
            # Fetch data and convert to list of dictionaries
            users = [dict(zip(columns, row)) for row in cursor.fetchall()]
            cursor.close()
            connection.close()
            return users
        except psycopg2.Error as e:
            print(f"Error: {e}")
            return []
    else:
        print("Failed to connect to the database.")
        return []
    

def fetch_user_subscription_data():
    conn = get_db_connection()

    # Queries to get counts
    query_total_users = 'SELECT COUNT(*) FROM "Users";'
    query_subscribed_users = 'SELECT COUNT(*) FROM "user_subscriptions" WHERE subscription_status = TRUE;'

    # Delta calculation: users who joined in the last 7 days
    query_delta_users = """
    SELECT COUNT(*) FROM "Users"
    WHERE CAST(date AS TIMESTAMP) >= NOW() - INTERVAL '7 days';
    """

    # Fetch the data
    total_users = int(pd.read_sql(query_total_users, conn).iloc[0, 0])
    subscribed_users = int(pd.read_sql(query_subscribed_users, conn).iloc[0, 0])
    delta = int(pd.read_sql(query_delta_users, conn).iloc[0, 0])
    delta_users = f"{delta} in the past week"

    # Close the database connection
    conn.close()

    return total_users, subscribed_users, delta_users


def fetch_user_joining_data():
    # Step 1: Connect to the PostgreSQL database
    conn = get_db_connection()

    # Step 2: Execute SQL query to fetch the date column
    # Use a SQL query to extract only the date part
    query = 'SELECT CAST(date AS DATE) AS date_only FROM "Users";'
    df = pd.read_sql(query, conn)

    conn.close()

    # Group by the date only and count the number of users per date
    df_grouped = df.groupby('date_only').size().reset_index(name='count')

    return df_grouped

def fetch_user_data(show_unsubscribed_only=False):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Query to fetch the necessary data
    query = """
    SELECT u.username, u.email, u.phone, us.subscription_status
    FROM "Users" u
    JOIN "user_subscriptions" us ON u.username = us.username
    """

    # If the toggle is on, filter to show only unsubscribed users
    if show_unsubscribed_only:
        query += " WHERE us.subscription_status = FALSE"

    # Execute the query
    cursor.execute(query)
    data = cursor.fetchall()

    # Create a DataFrame
    df = pd.DataFrame(data, columns=['username', 'email', 'phone', 'subscription_status'])

    # Close the database connection
    cursor.close()
    conn.close()

    return df


def update_subscription_status(username):
    conn = get_db_connection()
    cursor = conn.cursor()

    # SQL query to update subscription_status and last_active
    query = """
    UPDATE user_subscriptions
    SET subscription_status = TRUE, last_active = CURRENT_DATE + INTERVAL '30 days'
    WHERE username = %s
    """

    cursor.execute(query, (username,))
    conn.commit()

    cursor.close()
    conn.close()

    return cursor.rowcount