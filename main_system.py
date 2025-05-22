import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
from db import connect_db
from datetime import datetime

def open_main_system(user_id):
    app = tk.Tk()
    app.title("Calendar of Events")
    app.geometry("500x400")
    
    # Create tabs
    tab_control = ttk.Notebook(app)
    events_tab = ttk.Frame(tab_control)
    tab_control.add(events_tab, text="Events")
    
    # Status options
    event_statuses = ["Ongoing", "Completed", "Cancelled", "Postponed"]
    
    # Event type options
    event_types = ["Meeting", "Appointment", "Reminder", "Task", "Other"]

    def add_event():
        try:
            title = simpledialog.askstring("Event Title", "Enter event title:")
            if not title:
                return
                
            description = simpledialog.askstring("Description", "Enter description:")
            
            # Date input validation
            start_date = None
            while not start_date:
                start_str = simpledialog.askstring("Start Time", "Enter start time (YYYY-MM-DD HH:MM:SS):")
                if not start_str:
                    return
                try:
                    start_date = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    messagebox.showerror("Input Error", "Invalid date format. Use YYYY-MM-DD HH:MM:SS")
            
            end_date = None
            while not end_date:
                end_str = simpledialog.askstring("End Time", "Enter end time (YYYY-MM-DD HH:MM:SS):")
                if not end_str:
                    return
                try:
                    end_date = datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
                    if end_date <= start_date:
                        messagebox.showerror("Input Error", "End time must be after start time")
                        end_date = None
                except ValueError:
                    messagebox.showerror("Input Error", "Invalid date format. Use YYYY-MM-DD HH:MM:SS")
            
            # Type selection
            type_window = tk.Toplevel(app)
            type_window.title("Select Event Type")
            type_var = tk.StringVar(value=event_types[0])
            
            for t in event_types:
                tk.Radiobutton(type_window, text=t, variable=type_var, value=t).pack(anchor='w')
            
            def confirm_type():
                type_window.destroy()
            
            tk.Button(type_window, text="Confirm", command=confirm_type).pack(pady=10)
            app.wait_window(type_window)
            
            selected_type = type_var.get()
            status = "Ongoing"

            conn = connect_db()
            if not conn:
                messagebox.showerror("Database Error", "Could not connect to database")
                return
                
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO event (user_id, event_type, title, description, start_time, end_time, event_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_id, selected_type, title, description, start_str, end_str, status))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Event added successfully!")
            refresh_event_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add event: {e}")

    def show_event_details(event_id):
        try:
            conn = connect_db()
            if not conn:
                messagebox.showerror("Database Error", "Could not connect to database")
                return
                
            cursor = conn.cursor()
            cursor.execute("""
                SELECT title, description, event_type, start_time, end_time, event_status
                FROM event 
                WHERE event_id=%s AND user_id=%s
            """, (event_id, user_id))
            
            event = cursor.fetchone()
            
            # Get event summaries
            cursor.execute("""
                SELECT summary_text 
                FROM event_summary 
                WHERE event_id=%s
            """, (event_id,))
            
            summaries = cursor.fetchall()
            
            # Get event updates
            cursor.execute("""
                SELECT uploaded_at, update_reason 
                FROM event_update 
                WHERE event_id=%s
                ORDER BY uploaded_at DESC
            """, (event_id,))
            
            updates = cursor.fetchall()
            conn.close()
            
            if event:
                details_window = tk.Toplevel(app)
                details_window.title(f"Event: {event[0]}")
                details_window.geometry("500x400")
                
                # Event details
                tk.Label(details_window, text=f"Title: {event[0]}", anchor="w").pack(fill="x", padx=10, pady=5)
                tk.Label(details_window, text=f"Type: {event[2]}", anchor="w").pack(fill="x", padx=10)
                tk.Label(details_window, text=f"Status: {event[5]}", anchor="w").pack(fill="x", padx=10)
                tk.Label(details_window, text=f"Start: {event[3]}", anchor="w").pack(fill="x", padx=10)
                tk.Label(details_window, text=f"End: {event[4]}", anchor="w").pack(fill="x", padx=10)
                
                desc_frame = tk.LabelFrame(details_window, text="Description")
                desc_frame.pack(fill="both", expand=True, padx=10, pady=5)
                tk.Label(desc_frame, text=event[1] or "No description", anchor="w", wraplength=450).pack(fill="both", expand=True, padx=5, pady=5)
                
                # Summaries section
                if summaries:
                    summ_frame = tk.LabelFrame(details_window, text="Summaries")
                    summ_frame.pack(fill="both", expand=True, padx=10, pady=5)
                    for i, s in enumerate(summaries):
                        tk.Label(summ_frame, text=f"{i+1}. {s[0]}", anchor="w", wraplength=450).pack(fill="x", padx=5)
                
                # Updates section
                if updates:
                    update_frame = tk.LabelFrame(details_window, text="Updates")
                    update_frame.pack(fill="both", expand=True, padx=10, pady=5)
                    for u in updates:
                        tk.Label(update_frame, text=f"{u[0]}: {u[1]}", anchor="w", wraplength=450).pack(fill="x", padx=5)
                
                # Action buttons
                btn_frame = tk.Frame(details_window)
                btn_frame.pack(fill="x", padx=10, pady=10)
                
                # Update Status button
                tk.Button(btn_frame, text="Update Status", 
                          command=lambda: update_event_status(event_id, details_window)).pack(side="left", padx=5)
                
                # Add Summary button
                tk.Button(btn_frame, text="Add Summary", 
                          command=lambda: add_event_summary(event_id, details_window)).pack(side="left", padx=5)
                
                # Delete button
                tk.Button(btn_frame, text="Delete Event", 
                          command=lambda: delete_specific_event(event_id, details_window)).pack(side="left", padx=5)
                
            else:
                messagebox.showerror("Error", "Event not found or access denied")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show event details: {e}")

    def update_event_status(event_id, parent_window=None):
        try:
            status_window = tk.Toplevel(app)
            status_window.title("Update Event Status")
            
            status_var = tk.StringVar(value="Ongoing")
            
            for status in event_statuses:
                tk.Radiobutton(status_window, text=status, variable=status_var, value=status).pack(anchor="w")
            
            reason_frame = tk.Frame(status_window)
            reason_frame.pack(pady=10, fill="x", padx=10)
            
            tk.Label(reason_frame, text="Update Reason:").pack(anchor="w")
            reason_entry = tk.Entry(reason_frame, width=40)
            reason_entry.pack(fill="x")
            
            def confirm_status_update():
                try:
                    new_status = status_var.get()
                    reason = reason_entry.get().strip()
                    
                    if not reason:
                        messagebox.showerror("Input Error", "Please provide a reason for the update")
                        return
                    
                    conn = connect_db()
                    if not conn:
                        messagebox.showerror("Database Error", "Could not connect to database")
                        return
                        
                    cursor = conn.cursor()
                    # Update event status
                    cursor.execute("""
                        UPDATE event SET event_status = %s
                        WHERE event_id = %s AND user_id = %s
                    """, (new_status, event_id, user_id))
                    
                    # Add update record
                    cursor.execute("""
                        INSERT INTO event_update 
                        (event_id, updated_by, update_reason) 
                        VALUES (%s, %s, %s)
                    """, (event_id, f"User {user_id}", reason))
                    
                    conn.commit()
                    conn.close()
                    
                    messagebox.showinfo("Success", "Event status updated successfully")
                    status_window.destroy()
                    
                    # Refresh parent window if provided
                    if parent_window:
                        parent_window.destroy()
                        show_event_details(event_id)
                    
                    refresh_event_list()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to update status: {e}")
            
            tk.Button(status_window, text="Update", command=confirm_status_update).pack(pady=10)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open status update dialog: {e}")

    def add_event_summary(event_id, parent_window=None):
        try:
            # First verify the event belongs to the current user
            conn = connect_db()
            if not conn:
                messagebox.showerror("Database Error", "Could not connect to database")
                return
                
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM event 
                WHERE event_id=%s AND user_id=%s
            """, (event_id, user_id))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            if count == 0:
                messagebox.showerror("Access Denied", "You don't have permission to add a summary to this event")
                return
            
            summary = simpledialog.askstring("Summary", "Enter summary text:", parent=app)
            if not summary:
                return
                
            conn = connect_db()
            if not conn:
                messagebox.showerror("Database Error", "Could not connect to database")
                return
                
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO event_summary (event_id, summary_text) 
                VALUES (%s, %s)
            """, (event_id, summary))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Saved", "Event summary saved.")
            
            # Refresh parent window if provided
            if parent_window:
                parent_window.destroy()
                show_event_details(event_id)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add summary: {e}")

    def delete_specific_event(event_id, parent_window=None):
        try:
            if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this event?"):
                conn = connect_db()
                if not conn:
                    messagebox.showerror("Database Error", "Could not connect to database")
                    return
                    
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM event 
                    WHERE event_id=%s AND user_id=%s
                """, (event_id, user_id))
                conn.commit()
                conn.close()
                
                if cursor.rowcount > 0:
                    messagebox.showinfo("Deleted", "Event deleted successfully.")
                    if parent_window:
                        parent_window.destroy()
                    refresh_event_list()
                else:
                    messagebox.showinfo("Not Found", "Event not found or you don't have permission to delete it.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete event: {e}")

    def refresh_event_list():
        # Clear existing items
        for item in event_listbox.get_children():
            event_listbox.delete(item)
            
        try:
            conn = connect_db()
            if not conn:
                messagebox.showerror("Database Error", "Could not connect to database")
                return
                
            cursor = conn.cursor()
            cursor.execute("""
                SELECT event_id, title, event_type, event_status, start_time
                FROM event 
                WHERE user_id=%s
                ORDER BY start_time DESC
            """, (user_id,))
            
            events = cursor.fetchall()
            conn.close()
            
            for event in events:
                event_listbox.insert("", "end", text=str(event[0]), 
                                    values=(event[0], event[1], event[2], event[3], event[4]))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh event list: {e}")

    # Create event list view
    frame = ttk.Frame(events_tab)
    frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Create treeview for events
    event_listbox = ttk.Treeview(frame, columns=("ID", "Title", "Type", "Status", "Start Time"))
    event_listbox.heading("#0", text="")
    event_listbox.column("#0", width=0, stretch=tk.NO)
    event_listbox.heading("ID", text="ID")
    event_listbox.column("ID", width=30)
    event_listbox.heading("Title", text="Title")
    event_listbox.column("Title", width=150)
    event_listbox.heading("Type", text="Type")
    event_listbox.column("Type", width=80)
    event_listbox.heading("Status", text="Status")
    event_listbox.column("Status", width=80)
    event_listbox.heading("Start Time", text="Start Time")
    event_listbox.column("Start Time", width=150)
    
    # Add scrollbar
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=event_listbox.yview)
    event_listbox.configure(yscrollcommand=scrollbar.set)
    
    # Pack elements
    event_listbox.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Add double-click event
    event_listbox.bind("<Double-1>", lambda event: show_event_details(
        event_listbox.item(event_listbox.focus())["values"][0])
    )
    
    # Button frame
    button_frame = ttk.Frame(events_tab)
    button_frame.pack(fill="x", padx=10, pady=5)
    
    ttk.Button(button_frame, text="Add Event", command=add_event).pack(side="left", padx=5)
    ttk.Button(button_frame, text="Refresh", command=refresh_event_list).pack(side="left", padx=5)
    
    tab_control.pack(expand=1, fill="both")
    
    # Load initial data
    refresh_event_list()
    
    app.mainloop()
