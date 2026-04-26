from tkinter import messagebox, simpledialog, filedialog


class UICallback:
    def __init__(self, root=None):
        self.root = root

    def show_error(self, title, message, parent=None):
        messagebox.showerror(title, message, parent=parent or self.root)

    def show_warning(self, title, message, parent=None):
        messagebox.showwarning(title, message, parent=parent or self.root)

    def show_info(self, title, message, parent=None):
        messagebox.showinfo(title, message, parent=parent or self.root)

    def ask_yes_no(self, title, message, parent=None):
        return messagebox.askyesno(title, message, parent=parent or self.root)

    def ask_string(self, title, prompt, parent=None, initialvalue=""):
        return simpledialog.askstring(title, prompt, parent=parent or self.root, initialvalue=initialvalue or "")

    def ask_open_filename(self, title, filetypes):
        return filedialog.askopenfilename(title=title, filetypes=filetypes)
