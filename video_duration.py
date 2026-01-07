import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

VIDEO_EXTENSIONS = (".mp4", ".mov", ".mkv", ".avi", ".m4v", ".wmv")


# ------------------ Ressources (PyInstaller compatible) ------------------
def resource_path(relative_path):
    """Chemin correct en mode script ou app PyInstaller"""
    try:
        base_path = sys._MEIPASS  # PyInstaller
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def get_ffprobe_path():
    """Utilise ffprobe embarqué si présent, sinon ffprobe système"""
    embedded = resource_path("ffprobe")
    if os.path.exists(embedded):
        return embedded
    return "ffprobe"


# ------------------ ffprobe ------------------
def get_video_duration(path):
    try:
        result = subprocess.run(
            [
                get_ffprobe_path(),
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                path
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def format_time(seconds):
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def format_size(size):
    gb = size / (1024 ** 3)
    if gb >= 1:
        return f"{gb:.2f} Go"
    return f"{size / (1024 ** 2):.2f} Mo"


# ------------------ Tri colonnes ------------------
def sort_treeview(tree, col, reverse):
    rows = []
    for item in tree.get_children():
        value = tree.set(item, col)

        if col == "Durée":
            h, m, s = map(int, value.split(":"))
            key = h * 3600 + m * 60 + s
        elif col == "Taille":
            num, unit = value.split()
            key = float(num) * (1024 ** 3 if unit == "Go" else 1024 ** 2)
        else:
            key = value.lower()

        rows.append((key, item))

    rows.sort(reverse=reverse)
    for i, (_, item) in enumerate(rows):
        tree.move(item, "", i)

    tree.heading(col, command=lambda: sort_treeview(tree, col, not reverse))


# ------------------ Scan ------------------
def browse_folder():
    folder = filedialog.askdirectory(title="Sélectionner un dossier")
    if folder:
        folder_path.set(folder)
        scan_folder(folder)


def scan_folder(folder):
    tree.delete(*tree.get_children())

    recursive = recursive_var.get()
    total_duration = 0.0
    total_size = 0
    found = False

    if recursive:
        iterator = os.walk(folder)
    else:
        iterator = [(folder, [], os.listdir(folder))]

    for root, _, files in iterator:
        for f in files:
            if f.lower().endswith(VIDEO_EXTENSIONS):
                found = True
                full_path = os.path.join(root, f)

                duration = get_video_duration(full_path)
                size = os.path.getsize(full_path)

                total_duration += duration
                total_size += size

                tree.insert(
                    "",
                    "end",
                    values=(f, format_time(duration), format_size(size))
                )

    if not found:
        messagebox.showinfo("Aucune vidéo", "Aucun fichier vidéo trouvé.")
        label_total.config(text="Durée totale : 00:00:00 | Taille totale : 0 Mo")
        return

    label_total.config(
        text=f"Durée totale : {format_time(total_duration)}"
             f"   |   Taille totale : {format_size(total_size)}"
    )


# ------------------ GUI ------------------
root = tk.Tk()
root.title("Analyse des vidéos – macOS (ffprobe)")
root.geometry("780x480")

folder_path = tk.StringVar()
recursive_var = tk.BooleanVar(value=False)

top = ttk.Frame(root)
top.pack(fill="x", padx=10, pady=10)

ttk.Label(top, text="Dossier :").pack(side="left")
ttk.Entry(top, textvariable=folder_path, width=55).pack(side="left", padx=5)
ttk.Button(top, text="Parcourir…", command=browse_folder).pack(side="left")

ttk.Checkbutton(
    root,
    text="Inclure les sous-dossiers",
    variable=recursive_var
).pack(anchor="w", padx=20)

columns = ("Fichier", "Durée", "Taille")
tree = ttk.Treeview(root, columns=columns, show="headings")
tree.pack(fill="both", expand=True, padx=10, pady=10)

for c in columns:
    tree.heading(c, text=c, command=lambda col=c: sort_treeview(tree, col, False))

tree.column("Fichier", width=420)
tree.column("Durée", width=120, anchor="center")
tree.column("Taille", width=120, anchor="center")

label_total = ttk.Label(
    root,
    text="Durée totale : 00:00:00 | Taille totale : 0 Mo",
    font=("Helvetica", 11, "bold")
)
label_total.pack(pady=10)

root.mainloop()
