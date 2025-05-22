import tkinter as tk
from tkinter import messagebox, ttk
from db import connect_db
import main_system
import hashlib
import re

def encrypt_password(password):
    """Encrypt password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

def login():
    username = entry_username.get().strip()
    password = entry_password.get().strip()
    
    if not username or not password:
        messagebox.showerror("Error", "Please enter both username and password")
        return
    
    try:
        conn = connect_db()
        if not conn:
            messagebox.showerror("Database Error", "Could not connect to database")
            return
            
        cursor = conn.cursor()
        
        # Check if this is first login after DB update (old plaintext password)
        cursor.execute("SELECT user_id, password FROM user_info WHERE username=%s", (username,))
        user = cursor.fetchone()
        
        if not user:
            messagebox.showerror("Error", "Invalid username or password.")
            conn.close()
            return
            
        # Try both encrypted and non-encrypted password for backwards compatibility
        encrypted_password = encrypt_password(password)
        
        if user[1] == password:  # Old plaintext password
            # Update to encrypted password
            cursor.execute("UPDATE user_info SET password=%s WHERE user_id=%s", 
                          (encrypted_password, user[0]))
            conn.commit()
            print("Updated password to encrypted format")
            login_success = True
        elif user[1] == encrypted_password:  # New encrypted password
            login_success = True
        else:
            login_success = False
            
        conn.close()
        
        if login_success:
            messagebox.showinfo("Success", "Login successful!")
            root.destroy()
            main_system.open_main_system(user[0])
        else:
            messagebox.showerror("Error", "Invalid username or password.")
            
    except Exception as e:
        messagebox.showerror("Error", f"Login failed: {e}")

def register():
    top = tk.Toplevel()
    top.title("Register")
    top.geometry("350x400")
    
    frame = ttk.Frame(top, padding="10")
    frame.pack(fill="both", expand=True)
    
    # Create fields
    fields = {}
    field_labels = [
        "First Name", "Last Name", "Middle Initial", 
        "Username", "Email", "Phone Number", "Password",
        "Confirm Password"
    ]
    
    # Add fields with labels
    for i, label in enumerate(field_labels):
        ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w", pady=5)
        entry = ttk.Entry(frame, show="*" if "Password" in label else None)
        entry.grid(row=i, column=1, sticky="ew", padx=5, pady=5)
        fields[label] = entry
    
    # Configure grid to expand
    frame.columnconfigure(1, weight=1)
    
    def submit():
        # Get values and validate
        values = {}
        for field in field_labels:
            values[field] = fields[field].get().strip()
        
        # Check required fields
        if not all(values.values()):
            messagebox.showwarning("Input Error", "Please fill in all fields.")
            return
            
        # Validate email
        if not validate_email(values["Email"]):
            messagebox.showwarning("Input Error", "Please enter a valid email address.")
            return
            
        # Check passwords match
        if values["Password"] != values["Confirm Password"]:
            messagebox.showwarning("Input Error", "Passwords do not match.")
            return
            
        # Check password strength (minimum 8 characters)
        if len(values["Password"]) < 8:
            messagebox.showwarning("Input Error", "Password must be at least 8 characters.")
            return
        
        try:
            # Encrypt password
            encrypted_password = encrypt_password(values["Password"])
            
            conn = connect_db()
            if not conn:
                messagebox.showerror("Database Error", "Could not connect to database")
                return
                
            cursor = conn.cursor()
            
            # Check if email already exists
            cursor.execute("SELECT COUNT(*) FROM user_info WHERE user_email=%s", (values["Email"],))
            if cursor.fetchone()[0] > 0:
                messagebox.showerror("Error", "This email is already registered.")
                conn.close()
                return
                
            # Check if username already exists
            cursor.execute("SELECT COUNT(*) FROM user_info WHERE username=%s", (values["Username"],))
            if cursor.fetchone()[0] > 0:
                messagebox.showerror("Error", "This username is already taken.")
                conn.close()
                return
            
            cursor.execute("""
                INSERT INTO user_info (
                    first_name, last_name, middle_initial, 
                    username, user_email, phone_number, password
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                values["First Name"], 
                values["Last Name"], 
                values["Middle Initial"], 
                values["Username"], 
                values["Email"], 
                values["Phone Number"], 
                encrypted_password
            ))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Registered", "Registration successful! You can now login.")
            top.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Registration failed: {e}")

    # Add submit button
    ttk.Button(frame, text="Submit", command=submit).grid(row=len(field_labels), column=0, columnspan=2, pady=10)

# Main window
root = tk.Tk()
root.title("Calendar of Events - Login")
root.geometry("350x250")

main_frame = ttk.Frame(root, padding="20")
main_frame.pack(fill="both", expand=True)

ttk.Label(main_frame, text="Welcome to Calendar of Events", font=("Helvetica", 12, "bold")).pack(pady=10)

# Email field
ttk.Label(main_frame, text="Username").pack(anchor="w", pady=(10, 0))
entry_username = ttk.Entry(main_frame, width=30)
entry_username.pack(fill="x", pady=(0, 10))

# Password field
ttk.Label(main_frame, text="Password").pack(anchor="w")
entry_password = ttk.Entry(main_frame, show="*", width=30)
entry_password.pack(fill="x", pady=(0, 10))

# Button frame
button_frame = ttk.Frame(main_frame)
button_frame.pack(fill="x", pady=10)

# Login button
ttk.Button(button_frame, text="Login", command=login).pack(side="left", padx=(0, 10))

# Register button
ttk.Button(button_frame, text="Register", command=register).pack(side="left")

root.mainloop()
