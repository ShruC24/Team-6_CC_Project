import streamlit as st
import requests

# Sidebar menu
menu = st.sidebar.selectbox("Menu", ["Create Task", "Update Task", "Delete Task" , "View Tasks"])

# Input field for leader URL
leader_url = st.text_input("Leader Node URL", "http://127.0.1.1:5031")
leader_url = leader_url.rstrip('/') + "/fromLeader"

# Main content
if menu == "Create Task":
    st.header("Create Task")
    title = st.text_input("Title")
    task_status = st.selectbox("Status", ["IN_PROGRESS", "COMPLETED", "PENDING"])
    created_by = st.text_input("Created By")

    if st.button("Create Task"):
        data = {
            "TITLE": title,
            "TASK_STATUS": task_status,
            "CREATED_BY": created_by
        }
        headers = {"Content-Type": "application/json"}
        response = requests.post(leader_url, json=data, headers=headers)
        
        if response.status_code == 201:
            st.success("Task created successfully.")
        else:
            st.error("Failed to create task. Please check your input and try again.")

elif menu == "Update Task":
    st.header("Update Task")
    task_id = st.text_input("Task ID")
    title = st.text_input("New Title")
    task_status = st.selectbox("New Status", ["IN_PROGRESS", "COMPLETED", "PENDING"])
    created_by = st.text_input("New Created By")

    if st.button("Update Task"):
        data = {
            "TITLE": title,
            "TASK_STATUS": task_status,
            "CREATED_BY": created_by
        }
        headers = {"Content-Type": "application/json"}
        update_url = f"{leader_url}/{task_id}"
        response = requests.put(update_url, json=data, headers=headers)
        
        if response.status_code == 201:
            st.success("Task updated successfully.")
        else:
            st.error("Failed to update task. Please check your input and try again.")

elif menu == "Delete Task":
    st.header("Delete Task")
    task_id = st.text_input("Task ID")

    if st.button("Delete Task"):
        delete_url = f"{leader_url}/{task_id}"
        response = requests.delete(delete_url)
        
        if response.status_code == 201:
            st.success("Task deleted successfully.")
        else:
            st.error("Failed to delete task. Please check your input and try again.")

elif menu == "View Tasks":
    st.header("View Tasks")
    fetch_url = leader_url.replace("/fromLeader", "/confirmation")  # Modify URL for fetching tasks
    
    if st.button("Fetch Tasks"):
        response = requests.get(fetch_url)
        
        if response.status_code == 200:
            tasks = response.json()  # Assuming the response is JSON data
            st.write(tasks)  # Display the fetched tasks
        else:
            st.error(f"Failed to fetch tasks. Status code: {response.status_code}")
