import streamlit as st
import streamlit_authenticator as stauth
from dependencies import *

st.set_page_config(
    page_title="User Dashboard",
    page_icon="👨‍🦰",
    layout="wide",
    initial_sidebar_state="expanded")


def highlight_subscription_status(df):
    def apply_style(val):
        text_color = '#228B22' if val == 'Subscribed' else '#B22222'
        return f'color: {text_color}; font-weight: bold;'
    
    # Apply the styling function to the subscription_status column
    return df.style.applymap(apply_style, subset=['subscription_status'])


def login():
    # Extract usernames, hashed passwords, and names
    database = fetch_users()

    users = {}
    for user in database:
        username = user['username']
        password = user['password']
        email = user['email']
        users[username] = {
            'name': username,  # You can use other user information here
            'password': password,
            'email': email,
            'failed_login_attempts': 0,  # Will be managed automatically
            'logged_in': False  # Will be managed automatically
        }
        
    credentials = {
        "usernames": {}
    }
    for username, user_info in users.items():
        credentials["usernames"][username] = {
            "email": user_info["email"],
            "failed_login_attempts": 0,
            "logged_in": False,
            "name": username,
            "password": user_info["password"] 
        }

    # Now users is a dictionary with usernames as keys and user information dictionaries as values
    # Use this dictionary for initializing the Authenticator
    Authenticator = stauth.Authenticate(
        credentials,
        cookie_name="auth",
        cookie_key="abcdef",
        cookie_expiry_days=30
    )
    
    name, authentication_status, username = Authenticator.login()
    
    col1, col2 = st.columns(2)

    if authentication_status:
        with col1:
            st.markdown("""
                        <style>
                        .st-emotion-cache-1jzia57.e1nzilvr2 {
                            text-align: center;
                        }
                        .st-emotion-cache-1qffxr9.e1i5pmia2 {
                            background-color: #043B7B;
                        }
                        .st-emotion-cache-1wivap2.e1i5pmia3 {
                            background-color: #043B7B;
                            padding: 10px;
                            text-align: center;
                            font-weight: bold;
                        }
                        .st-emotion-cache-wnm74r.e1i5pmia0 {
                            background-color: #043B7B;
                            text-align: center;
                        }
                        </style>
                        """,unsafe_allow_html=True)
             
            # Fetch data from the database
            total_users, subscribed_users, delta_users = fetch_user_subscription_data()

            # Display metrics cards in Streamlit
            st.metric(label="Total Users", value=total_users, delta=delta_users)
            st.metric(label="Subscribed Users", value=subscribed_users, delta=delta_users)
            
            # Fetch the data
            df_grouped = fetch_user_joining_data()

            # Create a line chart
            st.line_chart(df_grouped.set_index('date_only')['count'])
                    
        with col2:
            st.markdown("""
                        <style>
                        .st-ae.st-bd.st-be.st-bf.st-bg.st-bh.st-bi.st-bj.st-bk.st-bl.st-bm.st-ah.st-bn.st-bo.st-bp.st-bq.st-br.st-bs.st-bt.st-bu.st-ax.st-ay.st-az.st-bv.st-b1.st-b2.st-bc.st-bw.st-bx.st-by {
                            background-color: #ffff;
                            color: black;
                        }
                        .st-emotion-cache-rkczhd.e1nzilvr4 {
                            color: #ffff;
                        }
                        .st-emotion-cache-6a6k5i.ef3psqc12 {
                            color: #ffff;
                            margin-top: 100px;
                            background-color: #F76212;
                            width: 100%;
                        }
                        .st-emotion-cache-6a6k5i.ef3psqc12:hover {
                            opacity: 0.9;
                            color: #ffff;
                        }
                        .st-emotion-cache-6a6k5i.ef3psqc12:active {
                            color: #ffff;
                        }
                        </style>
                        """, unsafe_allow_html=True)
            
            # Add a search bar
            search_query = st.text_input("Search by username, email, or phone")
            search_button = st.button("Search", type="primary")
            
            # Fetch data from the database with the option to show only unsubscribed users
            show_unsubscribed_only = st.toggle("Show only Unsubscribed Users")
            df = fetch_user_data(show_unsubscribed_only)

            # Filter the DataFrame based on the search query
            if search_query or search_button:
                df = df[df.apply(lambda row: search_query.lower() in row['username'].lower() 
                                 or search_query.lower() in row['email'].lower() 
                                 or search_query.lower() in row['phone'].lower(), axis=1)]

            # Map subscription_status to 'Subscribed' or 'Unsubscribed'
            df['subscription_status'] = df['subscription_status'].map({True: 'Subscribed', False: 'Unsubscribed'})
            
            # Pagination: Calculate the total number of pages
            total_rows = len(df)
            total_pages = (total_rows // 10) + (1 if total_rows % 10 > 0 else 0)
            
            # Get the start and end indices for the current page
            page_number = st.session_state.get("page_number", 1)  # Default to page 1 if not set
            start_idx = (page_number - 1) * 10
            end_idx = start_idx + 10

            # Slice the DataFrame to get only the rows for the current page
            df_paginated = df.iloc[start_idx:end_idx]

            # Display the paginated table with conditional formatting
            st.dataframe(highlight_subscription_status(df_paginated))

            # Add the selectbox for page numbers below the table
            page_number = st.selectbox("Page Number", range(1, total_pages + 1), index=page_number - 1)
            st.session_state["page_number"] = page_number

            with st.sidebar:
                st.title(f'Welcome {username}')
                # Add a search bar and button for adding a subscriber
                add_subscriber = st.text_input(label="Add New Subscriber")
                add_button = st.button(label="Add Subscriber", use_container_width=True, type='primary')

                if add_button and add_subscriber:
                    # Update the subscription status and last_active for the given username
                    rows_affected = update_subscription_status(add_subscriber)
                    
                    if rows_affected > 0:
                        st.success(f"Subscription updated for {add_subscriber}.")
                        st.balloons()
                    else:
                        st.error(f"User {add_subscriber} not found.")
                        
                st.markdown("""
                            ## Usage Guidelines
                            - Search User From the Search Bar.
                            - Copy & Paste the Username into the Box Above.
                            - Click the Add User Button.
                            - New Subscriber is Added.
                            """)
                Authenticator.logout()

    elif authentication_status == False:
        st.spinner('Please Wait...')
        st.error('Incorrect Username or Password')
    
    elif authentication_status == None:
        pass

st.markdown("""
            <style>
            .st-emotion-cache-1jzia57.e1nzilvr2 {
                text-align: center;
            }
            .st-emotion-cache-11t9mcj.ef3psqc7 {
                color: #ffff;
                background-color: #F76212;
                width: 100%;
            }
            .st-emotion-cache-11t9mcj.ef3psqc7:hover {
                opacity: 0.9;
                color: #ffff;
            }
            .st-emotion-cache-11t9mcj.ef3psqc7:active {
                color: #ffff;
            }
            .st-ae.st-bd.st-be.st-bf.st-bg.st-bh.st-bi.st-bj.st-bk.st-bl.st-bm.st-ah.st-bn.st-bo.st-bp.st-bq.st-br.st-bs.st-bt.st-bu.st-ax.st-ay.st-az.st-bv.st-b1.st-b2.st-bc.st-bw.st-bx.st-by {
                background-color: #ffff;
                color: black;
            }
            .st-emotion-cache-16h9saz.e10yg2by1 {
                padding: 50px;
                margin-left: 600px;
                margin-right: 600px;
                background-color: #043B7B;
            }
            </style>
            """, unsafe_allow_html=True)
st.title("User Dashboard")
login()
