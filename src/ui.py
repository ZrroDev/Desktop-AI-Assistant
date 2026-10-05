import tkinter as tk


# Functions
def on_submit(event=None):
    question = entry.get().strip()

    if not question:
        print("Question is empty")
        return
        
    print("question: " + question)
    print(f"include capture? {include_capture.get()}")

    # Clear entry and hide window
    entry.delete(0, tk.END)
    root.withdraw()
        

def on_escape(event=None):
    # Clear entry and hide window
    entry.delete(0, tk.END)
    root.withdraw()


# Windows and widgets
root = tk.Tk()

# Window details
root.title("Asistente")
root.attributes("-topmost", True)

# Question for the assistant entry
entry = tk.Entry(root, width=100)
entry.pack(padx=10, pady=10)
entry.focus_set()

# Button to select send the capture to the assistant 
include_capture = tk.BooleanVar(value=True)
tk.Checkbutton(root, text="Incluir captura", variable=include_capture).pack()

# Submit button
tk.Button(root, text="Enviar", command=on_submit).pack()

# Key bindings
root.bind("<Return>", on_submit)
root.bind("<Escape>", on_escape)

# Main loop run
if __name__ == "__main__": 
    root.mainloop()