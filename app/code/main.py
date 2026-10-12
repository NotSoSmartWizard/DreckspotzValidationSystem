import customtkinter as ctk
from gui import create_main_frame

if __name__ == "__main__":
    app = ctk.CTk()
    create_main_frame(app)
    app.mainloop()
