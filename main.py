# -*- coding: utf-8 -*-
"""
Contacts Personnels Premium
Application Kivy : contacts locaux, favoris, recherche, notes et sauvegarde JSON.
Les contacts sont stockés dans contacts.json dans le dossier privé de l'application.
"""
import json
import os
import shutil
import webbrowser
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.utils import platform

APP_BG = (0.045, 0.065, 0.12, 1)
CARD_BG = (0.085, 0.12, 0.20, 1)
BLUE = (0.20, 0.48, 0.98, 1)
TEAL = (0.10, 0.76, 0.72, 1)
RED = (0.92, 0.25, 0.32, 1)
WHITE = (0.95, 0.97, 1, 1)
MUTED = (0.65, 0.71, 0.82, 1)

def safe_text(value):
    return str(value or "").strip()

class ContactsApp(App):
    title = "Contacts Premium"

    def build(self):
        Window.clearcolor = APP_BG
        self.contacts = []
        self.selected_filter = "Tous"
        self.data_path = os.path.join(self.user_data_dir, "contacts.json")
        self.load_contacts()

        root = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        header = BoxLayout(size_hint_y=None, height=dp(58), spacing=dp(10))
        title_box = BoxLayout(orientation="vertical", spacing=dp(1))
        title_box.add_widget(Label(text="[b]MES CONTACTS[/b]", markup=True, color=WHITE,
                                   font_size="23sp", halign="left", valign="middle"))
        title_box.add_widget(Label(text="Votre carnet personnel", color=MUTED,
                                   font_size="12sp", halign="left", valign="middle"))
        header.add_widget(title_box)
        header.add_widget(self.make_button("＋ Ajouter", BLUE, self.open_add, width=dp(110)))
        root.add_widget(header)

        self.search = TextInput(hint_text="⌕  Rechercher un nom, téléphone…",
                                multiline=False, size_hint_y=None, height=dp(48),
                                background_normal="", background_active="",
                                background_color=CARD_BG, foreground_color=WHITE,
                                hint_text_color=MUTED, cursor_color=TEAL,
                                padding=[dp(14), dp(13), dp(14), dp(10)], font_size="15sp")
        self.search.bind(text=lambda *_: self.refresh_list())
        root.add_widget(self.search)

        tabs = GridLayout(cols=3, spacing=dp(7), size_hint_y=None, height=dp(42))
        for name in ("Tous", "Favoris", "Sauvegarde"):
            action = self.export_backup if name == "Sauvegarde" else lambda n=name: self.set_filter(n)
            tabs.add_widget(self.make_button(name, TEAL if name == self.selected_filter else CARD_BG, action))
        root.add_widget(tabs)

        self.count_label = Label(text="", color=MUTED, size_hint_y=None, height=dp(24),
                                 halign="left", valign="middle", font_size="12sp")
        root.add_widget(self.count_label)

        self.scroll = ScrollView(do_scroll_x=False, bar_width=dp(4))
        self.list_box = GridLayout(cols=1, spacing=dp(9), size_hint_y=None, padding=[0, 0, 0, dp(8)])
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        self.scroll.add_widget(self.list_box)
        root.add_widget(self.scroll)

        footer = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(44))
        footer.add_widget(self.make_button("Importer une sauvegarde", CARD_BG, self.import_backup))
        footer.add_widget(self.make_button("Exporter mes contacts", CARD_BG, self.export_backup))
        root.add_widget(footer)

        self.refresh_list()
        return root

    def make_button(self, text, color, callback, width=None):
        btn = Button(text=text, size_hint_x=None if width else 1, width=width or 0,
                     size_hint_y=None, height=dp(42), background_normal="",
                     background_down="", background_color=color, color=WHITE,
                     font_size="13sp", bold=True)
        btn.bind(on_release=lambda *_: callback())
        return btn

    def load_contacts(self):
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.contacts = data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError):
            self.contacts = []

    def save_contacts(self):
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump(self.contacts, f, ensure_ascii=False, indent=2)

    def set_filter(self, name):
        self.selected_filter = name
        # Rafraîchir la couleur des onglets en reconstruisant l'écran est inutile;
        # la liste change immédiatement et l'onglet sélectionné reste indiqué dans le compteur.
        self.refresh_list()

    def refresh_list(self):
        if not hasattr(self, "list_box"):
            return
        self.list_box.clear_widgets()
        query = safe_text(self.search.text).lower() if hasattr(self, "search") else ""
        shown = []
        for c in self.contacts:
            if self.selected_filter == "Favoris" and not c.get("favorite"):
                continue
            searchable = " ".join([safe_text(c.get(k)) for k in ("first", "last", "phone", "email", "company")]).lower()
            if query and query not in searchable:
                continue
            shown.append(c)
        shown.sort(key=lambda c: (not bool(c.get("favorite")), safe_text(c.get("last")).lower(), safe_text(c.get("first")).lower()))
        self.count_label.text = f"{len(shown)} contact(s)  •  {self.selected_filter}"
        if not shown:
            self.list_box.add_widget(Label(text="Aucun contact pour le moment.\nAppuyez sur « Ajouter » pour commencer.",
                                           color=MUTED, halign="center", valign="middle",
                                           size_hint_y=None, height=dp(120), font_size="14sp"))
        for c in shown:
            self.list_box.add_widget(self.contact_card(c))

    def contact_card(self, contact):
        card = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(7),
                         size_hint_y=None, height=dp(148))
        # Kivy Button/BoxLayout background isn't directly stylable; a dark button-like panel is used.
        top = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(8))
        initials = (safe_text(contact.get("first"))[:1] + safe_text(contact.get("last"))[:1]).upper() or "?"
        avatar = Label(text=f"[b]{initials}[/b]", markup=True, size_hint_x=None, width=dp(42),
                       color=WHITE, font_size="16sp")
        top.add_widget(avatar)
        fullname = (safe_text(contact.get("first")) + " " + safe_text(contact.get("last"))).strip() or "Sans nom"
        name = Label(text=f"[b]{fullname}[/b]" + ("  ★" if contact.get("favorite") else ""),
                     markup=True, color=WHITE, font_size="16sp", halign="left", valign="middle")
        name.bind(size=lambda w, s: setattr(w, "text_size", s))
        top.add_widget(name)
        top.add_widget(self.make_button("Modifier", BLUE, lambda c=contact: self.open_edit(c), width=dp(84)))
        card.add_widget(top)
        details = "  •  ".join(x for x in [safe_text(contact.get("phone")), safe_text(contact.get("email"))] if x)
        if not details:
            details = "Aucun numéro ni e-mail renseigné"
        lab = Label(text=details, color=MUTED, font_size="12sp", halign="left", valign="middle",
                    size_hint_y=None, height=dp(22))
        lab.bind(size=lambda w, s: setattr(w, "text_size", s))
        card.add_widget(lab)
        actions = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(7))
        if safe_text(contact.get("phone")):
            actions.add_widget(self.make_button("Appeler", TEAL, lambda c=contact: self.call_contact(c)))
            actions.add_widget(self.make_button("SMS", BLUE, lambda c=contact: self.sms_contact(c)))
        actions.add_widget(self.make_button("★" if contact.get("favorite") else "☆",
                                            (0.75, 0.52, 0.12, 1), lambda c=contact: self.toggle_favorite(c), width=dp(46)))
        actions.add_widget(self.make_button("Supprimer", RED, lambda c=contact: self.confirm_delete(c)))
        card.add_widget(actions)

        # Panel is a Button with custom color behind the card content.
        panel = BoxLayout(orientation="vertical", padding=dp(1), size_hint_y=None, height=dp(150))
        bg = Button(text="", disabled=True, background_normal="", background_color=CARD_BG)
        # Use a simple vertical container; card content is rendered above the dark background.
        # Kivy widget layering is handled by a wrapper with a colored canvas.
        from kivy.graphics import Color, RoundedRectangle
        with panel.canvas.before:
            Color(*CARD_BG)
            panel._rounded = RoundedRectangle(pos=panel.pos, size=panel.size, radius=[dp(14)])
        panel.bind(pos=lambda w, p: setattr(w._rounded, "pos", p),
                   size=lambda w, s: setattr(w._rounded, "size", s))
        panel.add_widget(card)
        return panel

    def open_add(self):
        self.open_form({})

    def open_edit(self, contact):
        self.open_form(contact)

    def open_form(self, existing):
        is_edit = bool(existing)
        content = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(8))
        fields = {}
        specs = [("first", "Prénom"), ("last", "Nom"), ("phone", "Téléphone"),
                 ("email", "E-mail"), ("company", "Société / catégorie"), ("notes", "Notes personnelles")]
        for key, hint in specs:
            field = TextInput(text=safe_text(existing.get(key)), hint_text=hint,
                              multiline=(key == "notes"), size_hint_y=None,
                              height=dp(76 if key == "notes" else 43),
                              background_normal="", background_active="", background_color=CARD_BG,
                              foreground_color=WHITE, hint_text_color=MUTED, cursor_color=TEAL,
                              padding=[dp(10), dp(10), dp(10), dp(8)], font_size="14sp")
            fields[key] = field
            content.add_widget(field)
        buttons = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        popup = Popup(title="Modifier le contact" if is_edit else "Nouveau contact",
                      content=content, size_hint=(0.94, 0.90), auto_dismiss=False,
                      background_color=APP_BG, title_color=WHITE)
        buttons.add_widget(self.make_button("Annuler", CARD_BG, popup.dismiss))
        def save():
            if not safe_text(fields["first"].text) and not safe_text(fields["last"].text) and not safe_text(fields["phone"].text):
                self.message("Informations manquantes", "Ajoute au moins un nom, un prénom ou un numéro.")
                return
            record = dict(existing) if is_edit else {"id": datetime.now().strftime("%Y%m%d%H%M%S%f"), "favorite": False}
            for key, widget in fields.items():
                record[key] = safe_text(widget.text)
            if is_edit:
                for i, item in enumerate(self.contacts):
                    if item.get("id") == existing.get("id"):
                        self.contacts[i] = record
                        break
            else:
                self.contacts.append(record)
            self.save_contacts()
            popup.dismiss()
            self.refresh_list()
        buttons.add_widget(self.make_button("Enregistrer", BLUE, save))
        content.add_widget(buttons)
        popup.open()

    def toggle_favorite(self, contact):
        contact["favorite"] = not bool(contact.get("favorite"))
        self.save_contacts()
        self.refresh_list()

    def confirm_delete(self, contact):
        fullname = (safe_text(contact.get("first")) + " " + safe_text(contact.get("last"))).strip() or "ce contact"
        box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(12))
        box.add_widget(Label(text=f"Supprimer {fullname} ?", color=WHITE))
        popup = Popup(title="Confirmation", content=box, size_hint=(0.85, 0.28),
                      background_color=APP_BG, title_color=WHITE)
        row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        row.add_widget(self.make_button("Annuler", CARD_BG, popup.dismiss))
        def delete():
            self.contacts = [c for c in self.contacts if c.get("id") != contact.get("id")]
            self.save_contacts()
            popup.dismiss()
            self.refresh_list()
        row.add_widget(self.make_button("Supprimer", RED, delete))
        box.add_widget(row)
        popup.open()

    def call_contact(self, contact):
        phone = safe_text(contact.get("phone"))
        if not phone:
            self.message("Numéro manquant", "Ajoute un numéro de téléphone à ce contact.")
            return
        if platform == "android":
            try:
                from jnius import autoclass
                Intent = autoclass("android.content.Intent")
                Uri = autoclass("android.net.Uri")
                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                intent = Intent(Intent.ACTION_DIAL, Uri.parse("tel:" + phone))
                PythonActivity.mActivity.startActivity(intent)
                return
            except Exception as e:
                self.message("Appel", "Impossible d'ouvrir le composeur : " + str(e))
                return
        self.message("Appel téléphonique", "Sur ordinateur, l'appel n'est pas lancé. Numéro : " + phone)

    def sms_contact(self, contact):
        phone = safe_text(contact.get("phone"))
        if platform == "android":
            try:
                from jnius import autoclass
                Intent = autoclass("android.content.Intent")
                Uri = autoclass("android.net.Uri")
                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                intent = Intent(Intent.ACTION_SENDTO, Uri.parse("smsto:" + phone))
                PythonActivity.mActivity.startActivity(intent)
                return
            except Exception as e:
                self.message("SMS", "Impossible d'ouvrir l'application SMS : " + str(e))
                return
        self.message("SMS", "Sur ordinateur, le SMS n'est pas lancé. Numéro : " + phone)

    def message(self, title, text):
        box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        box.add_widget(Label(text=text, color=WHITE))
        popup = Popup(title=title, content=box, size_hint=(0.88, 0.35),
                      background_color=APP_BG, title_color=WHITE)
        box.add_widget(self.make_button("OK", BLUE, popup.dismiss))
        popup.open()

    def export_backup(self):
        # Copie JSON vers un emplacement visible si disponible; sinon affiche l'emplacement privé.
        try:
            if platform == "android":
                from android.storage import primary_external_storage_path
                target_dir = os.path.join(primary_external_storage_path(), "Download")
            else:
                target_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            os.makedirs(target_dir, exist_ok=True)
            filename = "contacts_personnels_sauvegarde_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".json"
            target = os.path.join(target_dir, filename)
            with open(target, "w", encoding="utf-8") as f:
                json.dump(self.contacts, f, ensure_ascii=False, indent=2)
            self.message("Sauvegarde créée", "Fichier enregistré ici :\n" + target)
        except Exception:
            self.message("Sauvegarde", "Les contacts sont conservés dans le dossier privé de l'application.\n" + self.data_path)

    def import_backup(self):
        content = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        content.add_widget(Label(text="Pour importer, place un fichier JSON de sauvegarde dans le dossier de téléchargement, puis saisis son chemin complet ci-dessous.", color=WHITE))
        path_input = TextInput(hint_text="/chemin/vers/contacts.json", multiline=False,
                               size_hint_y=None, height=dp(44), background_normal="",
                               background_color=CARD_BG, foreground_color=WHITE, hint_text_color=MUTED)
        content.add_widget(path_input)
        popup = Popup(title="Importer une sauvegarde", content=content, size_hint=(0.94, 0.45),
                      background_color=APP_BG, title_color=WHITE)
        row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        row.add_widget(self.make_button("Annuler", CARD_BG, popup.dismiss))
        def do_import():
            path = safe_text(path_input.text)
            if not path or not os.path.isfile(path):
                self.message("Fichier introuvable", "Vérifie le chemin du fichier JSON.")
                return
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, list):
                    raise ValueError("Le fichier doit contenir une liste de contacts.")
                # Fusion par identifiant, sans effacer les contacts déjà présents.
                by_id = {c.get("id"): c for c in self.contacts if c.get("id")}
                for item in data:
                    if isinstance(item, dict):
                        item.setdefault("id", datetime.now().strftime("%Y%m%d%H%M%S%f"))
                        by_id[item["id"]] = item
                self.contacts = list(by_id.values())
                self.save_contacts()
                popup.dismiss()
                self.refresh_list()
                self.message("Import terminé", f"{len(data)} contact(s) importé(s).")
            except Exception as e:
                self.message("Erreur d'import", str(e))
        row.add_widget(self.make_button("Importer", BLUE, do_import))
        content.add_widget(row)
        popup.open()

if __name__ == "__main__":
    ContactsApp().run()
