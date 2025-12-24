import os
os.environ['KIVY_NO_ARGS'] = '1'

from kivy.config import Config
Config.set('graphics', 'width', '360')
Config.set('graphics', 'height', '740')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.properties import ListProperty, NumericProperty, BooleanProperty
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.utils import platform
from datetime import datetime

# PDF Library
try:
    from fpdf import FPDF
except ImportError:
    class FPDF:
        def __init__(self, *args, **kwargs):
            raise ImportError("The 'fpdf2' library is missing. Run 'pip install fpdf2'")

# Garden Import
try:
    from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
except:
    FigureCanvasKivyAgg = None

# --- AIRCRAFT SPECIFICS: G-CMCY ---
AC_TYPE = "P2012 Traveller"
AC_REG = "G-CMCY"
APP_VERSION = "V1"
ENVELOPE_MAC = [18, 18, 22.5, 31, 31, 18, 18] 
ENVELOPE_MASS = [2400, 3000, 3680, 3680, 2400, 2400, 2400]

BOM_MASS = 2563.7
BOM_ARM = 0.389
MAC_LENGTH = 1.839

# LIMITS
MZFM_LIMIT = 3560
MTOM_LIMIT = 3680
MLND_LIMIT = 3630

# Stations
SECOND_PILOT_ARM = -1.739
PAX_ROW_LABELS = ["R1 L", "R1 R", "R2 L", "R2 R", "R3 L", "R3 R", "R4 L", "R4 R", "R5 R"]
PAX_ROW_ARMS = [-0.707, 0.106, 0.919, 1.732, 2.545]
FOR_BAGGAGE_ARM = -3.345
AFT_BAGGAGE_ARM = 3.539
TKS_ARM = 1.495
FUEL_ARM = 0.787

KV = """
<StyledInput@TextInput>:
    multiline: False
    input_filter: 'float'
    padding_y: [12, 12]
    background_normal: ''
    background_color: [0.92, 0.94, 0.96, 1]
    foreground_color: [0.1, 0.2, 0.3, 1]
    cursor_color: [0.1, 0.4, 0.8, 1]

<LabelRow@BoxLayout>:
    orientation: 'horizontal'
    spacing: 10
    size_hint_y: None
    height: '45dp'

<SectionHeader@Label>:
    size_hint_y: None
    height: '30dp'
    halign: 'left'
    text_size: self.size
    bold: True
    color: [0.1, 0.4, 0.8, 1]
    font_size: '14sp'

<TecnamLayout>:
    orientation: "vertical"
    padding: 15
    spacing: 12
    size_hint_y: None
    height: self.minimum_height
    canvas.before:
        Color:
            rgba: [0.96, 0.97, 0.98, 1]
        Rectangle:
            pos: self.pos
            size: self.size

    # HEADER LOGO & TIME
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: '80dp'
        Image:
            source: 'static/logo.jpg'
            size_hint_x: 0.4
            allow_stretch: True
            keep_ratio: True
        BoxLayout:
            orientation: 'vertical'
            Label:
                text: "G-CMCY LOADMASTER"
                bold: True
                color: [0.05, 0.1, 0.2, 1]
                font_size: '18sp'
                halign: 'right'
                text_size: self.size
            Label:
                id: time_label
                text: ""
                color: [0.4, 0.5, 0.6, 1]
                font_size: '12sp'
                halign: 'right'
                text_size: self.size

    # PILOT INFO
    SectionHeader:
        text: "FLIGHT DATA"
    
    BoxLayout:
        orientation: 'vertical'
        size_hint_y: None
        height: self.minimum_height
        spacing: 8
        LabelRow:
            Label:
                text: "Captain:"
                color: [0.2, 0.3, 0.4, 1]
            StyledInput:
                id: captain_input
                input_filter: None
        LabelRow:
            Label:
                text: "Prepared By:"
                color: [0.2, 0.3, 0.4, 1]
            StyledInput:
                id: preparer_input
                input_filter: None
        LabelRow:
            Label:
                text: "2nd Pilot (85kg):"
                color: [0.2, 0.3, 0.4, 1]
            ToggleButton:
                id: pilot_toggle
                text: "NOT PRESENT" if self.state == 'normal' else "ON BOARD"
                background_normal: ''
                background_color: [0.1, 0.4, 0.8, 1] if self.state == 'down' else [0.7, 0.7, 0.7, 1]
                on_state: root.has_second_pilot = (self.state == 'down'); root.calculate()

    # SEATING GRID
    SectionHeader:
        text: "PASSENGER CONFIGURATION"
    GridLayout:
        id: seat_grid
        cols: 2
        spacing: 10
        size_hint_y: None
        height: '300dp'

    # CARGO & FUEL
    SectionHeader:
        text: "BAGGAGE, TKS & FUEL"
    GridLayout:
        cols: 4
        spacing: 10
        size_hint_y: None
        height: '160dp'
        Label:
            text: "Fwd (103):"
            color: [0,0,0,1]
        StyledInput:
            id: fwd_input
            on_text: root.validate_input('fwd', self.text)
        Label:
            text: "Aft (239):"
            color: [0,0,0,1]
        StyledInput:
            id: aft_input
            on_text: root.validate_input('aft', self.text)
        Label:
            text: "TKS (60):"
            color: [0,0,0,1]
        StyledInput:
            id: tks_input
            on_text: root.validate_input('tks', self.text)
        Label:
            text: "Fuel (540):"
            color: [0,0,0,1]
        StyledInput:
            id: fuel_input
            on_text: root.validate_input('fuel', self.text)
        Label:
            text: "Burn (kg):"
            color: [0,0,0,1]
        StyledInput:
            id: burn_input
            on_text: root.validate_input('burn', self.text)
        Widget:

    # LIVE RESULTS
    BoxLayout:
        size_hint_y: None
        height: '60dp'
        canvas.before:
            Color:
                rgba: [0.1, 0.15, 0.25, 1]
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [10,]
        Label:
            id: zfm_mass_label
            text: "ZFM: --"
            bold: True
        Label:
            id: ramp_mass_label
            text: "TOW: --"
            bold: True
        Label:
            id: lnd_mass_label
            text: "LND: --"
            bold: True

    # STATUS BANNER
    BoxLayout:
        id: status_banner
        size_hint_y: None
        height: '50dp'
        canvas.before:
            Color:
                rgba: root.banner_color
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [10,]
        Label:
            id: result_label
            text: "WAITING..."
            bold: True
            font_size: '18sp'

    # GRAPH
    BoxLayout:
        id: plot_box
        size_hint_y: None
        height: '350dp'

    # ACTIONS
    Button:
        text: "GENERATE LOAD SHEET"
        size_hint_y: None
        height: '65dp'
        background_normal: ''
        background_color: [0.1, 0.6, 0.3, 1]
        bold: True
        on_release: root.export_to_pdf()
    
    Button:
        text: "RESET ALL FIELDS"
        size_hint_y: None
        height: '45dp'
        background_normal: ''
        background_color: [0.8, 0.3, 0.3, 1]
        on_release: root.reset_form()
"""

class TecnamLayout(BoxLayout):
    SEAT_TYPES = [
        ("EMPTY", 0, [0.8, 0.8, 0.8, 1]),
        ("MALE", 90, [0.1, 0.4, 0.8, 1]),
        ("FEMALE", 72, [0.8, 0.3, 0.6, 1]),
        ("CHILD", 35, [0.3, 0.7, 0.8, 1])
    ]
    
    has_second_pilot = BooleanProperty(False)
    for_baggage = NumericProperty(0)
    aft_baggage = NumericProperty(0)
    ramp_fuel = NumericProperty(0)
    fuel_burn = NumericProperty(0)
    tks = NumericProperty(0)
    banner_color = ListProperty([0.2, 0.2, 0.2, 1])
    current_results = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.seat_states = [0] * 9 
        Clock.schedule_once(self.setup_seats, 0.1)
        Clock.schedule_interval(self.update_time, 1)

    def update_time(self, dt):
        self.ids.time_label.text = datetime.now().strftime("%d %b %Y | %H:%M")

    def setup_seats(self, dt):
        grid = self.ids.seat_grid
        grid.clear_widgets()
        for i in range(8):
            btn = Button(text=f"{PAX_ROW_LABELS[i]}\nEMPTY", background_normal='',
                         background_color=self.SEAT_TYPES[0][2],
                         halign='center', font_size='11sp', bold=True)
            btn.bind(on_release=lambda instance, idx=i: self.cycle_seat(idx, instance))
            grid.add_widget(btn)
        grid.add_widget(Widget()) 
        btn9 = Button(text=f"{PAX_ROW_LABELS[8]}\nEMPTY", background_normal='',
                      background_color=self.SEAT_TYPES[0][2],
                      halign='center', font_size='11sp', bold=True)
        btn9.bind(on_release=lambda instance, idx=8: self.cycle_seat(idx, instance))
        grid.add_widget(btn9)
        self.calculate()

    def cycle_seat(self, idx, btn):
        self.seat_states[idx] = (self.seat_states[idx] + 1) % len(self.SEAT_TYPES)
        name, _, color = self.SEAT_TYPES[self.seat_states[idx]]
        btn.text = f"{PAX_ROW_LABELS[idx]}\n{name}"
        btn.background_color = color 
        self.calculate()

    def validate_input(self, type, val):
        try:
            num = float(val or 0)
            if type == 'fwd': self.for_baggage = num
            elif type == 'aft': self.aft_baggage = num
            elif type == 'fuel': self.ramp_fuel = num
            elif type == 'burn': self.fuel_burn = num
            elif type == 'tks': self.tks = num
            self.calculate()
        except: pass

    def calculate(self, *args):
        zfm_mass = BOM_MASS + self.for_baggage + self.aft_baggage + self.tks
        zfm_mom = (BOM_MASS * BOM_ARM) + (self.for_baggage * FOR_BAGGAGE_ARM) + \
                  (self.aft_baggage * AFT_BAGGAGE_ARM) + (self.tks * TKS_ARM)
        if self.has_second_pilot:
            zfm_mass += 85
            zfm_mom += (85 * SECOND_PILOT_ARM)
        for i, state in enumerate(self.seat_states):
            weight = self.SEAT_TYPES[state][1]
            zfm_mass += weight
            zfm_mom += weight * PAX_ROW_ARMS[i // 2]

        zfm_mac = ((zfm_mom / zfm_mass) * 100) / MAC_LENGTH if zfm_mass > 0 else 0
        ramp_mass = zfm_mass + self.ramp_fuel
        ramp_mom = zfm_mom + (self.ramp_fuel * FUEL_ARM)
        ramp_mac = ((ramp_mom / ramp_mass) * 100) / MAC_LENGTH if ramp_mass > 0 else 0
        lnd_mass = ramp_mass - self.fuel_burn
        lnd_mom = ramp_mom - (self.fuel_burn * FUEL_ARM)
        lnd_mac = ((lnd_mom / lnd_mass) * 100) / MAC_LENGTH if lnd_mass > 0 else 0
        lnd_fuel = self.ramp_fuel - self.fuel_burn

        self.ids.zfm_mass_label.text = f"ZFM: {zfm_mass:.0f}kg"
        self.ids.ramp_mass_label.text = f"TOW: {ramp_mass:.0f}kg"
        self.ids.lnd_mass_label.text = f"LND: {lnd_mass:.0f}kg"
        
        envelope_path = Path(list(zip(ENVELOPE_MAC, ENVELOPE_MASS)))
        is_safe = (envelope_path.contains_point((zfm_mac, zfm_mass)) and 
                   zfm_mass <= MZFM_LIMIT and 
                   ramp_mass <= MTOM_LIMIT and 
                   lnd_mass <= MLND_LIMIT)
        
        self.ids.result_label.text = f"LOAD SAFE: {zfm_mac:.1f}% MAC" if is_safe else "LOAD UNSAFE / OVERWEIGHT"
        self.banner_color = [0.1, 0.6, 0.3, 1] if is_safe else [0.8, 0.2, 0.2, 1]
        
        self.current_results = {
            "zfm_m": zfm_mass, "zfm_mac": zfm_mac, "ramp_m": ramp_mass, "ramp_mac": ramp_mac, 
            "lnd_m": lnd_mass, "lnd_mac": lnd_mac, "time": self.ids.time_label.text,
            "fwd": self.for_baggage, "aft": self.aft_baggage, "fuel": self.ramp_fuel, 
            "burn": self.fuel_burn, "lnd_fuel": lnd_fuel, "tks": self.tks
        }
        self.update_plot(zfm_mac, zfm_mass, ramp_mac, ramp_mass, lnd_mac, lnd_mass)

    def update_plot(self, z_mac, z_m, r_mac, r_m, l_mac, l_m):
        if not FigureCanvasKivyAgg: return
        self.ids.plot_box.clear_widgets()
        plt.clf()
        plt.plot(ENVELOPE_MAC, ENVELOPE_MASS, color='#2c3e50', lw=2)
        plt.fill(ENVELOPE_MAC, ENVELOPE_MASS, alpha=0.1, color='#3498db')
        
        plt.axhline(y=MTOM_LIMIT, color='#e74c3c', linestyle='--', alpha=0.5, label='MTOM')
        plt.axhline(y=MLND_LIMIT, color='#f39c12', linestyle='--', alpha=0.5, label='MLND')
        plt.axhline(y=MZFM_LIMIT, color='#2980b9', linestyle='--', alpha=0.5, label='MZFM')

        plt.plot(z_mac, z_m, 'ks', label='ZFM', markersize=5)
        plt.plot(r_mac, r_m, 'ro', label='TOW', markersize=7)
        plt.plot(l_mac, l_m, 'gx', label='LND', markersize=7, mew=2)
        
        plt.xlabel("Center of Gravity (% MAC)", fontsize=9, fontweight='bold')
        plt.ylabel("Weight (kg)", fontsize=9, fontweight='bold')
        plt.xlim(15, 35); plt.ylim(2300, 3900); plt.grid(True, linestyle=':', alpha=0.5)
        plt.legend(loc='upper right', fontsize='7', frameon=True)
        self.ids.plot_box.add_widget(FigureCanvasKivyAgg(plt.gcf()))

    def export_to_pdf(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"GCMCY_LoadSheet_{timestamp}.pdf"
        path = os.path.join("/storage/emulated/0/Download", filename) if os.name == 'posix' else os.path.join(os.getcwd(), filename)
        temp_plot_path = "temp_plot.png"
        try:
            plt.savefig(temp_plot_path, dpi=200)
            pdf = FPDF()
            pdf.add_page()
            
            if os.path.exists('static/logo.jpg'):
                pdf.image('static/logo.jpg', x=10, y=8, w=45)
            
            pdf.set_font("Helvetica", 'B', 16)
            pdf.set_y(10)
            pdf.set_text_color(20, 50, 100)
            pdf.cell(0, 10, txt=f"{AC_REG} - ELECTRONIC LOAD SHEET", ln=True, align='R')
            pdf.set_font("Helvetica", size=9)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 5, txt=f"Aircraft: {AC_TYPE} | Version: {APP_VERSION}", ln=True, align='R'); pdf.ln(10)

            pdf.set_fill_color(220, 230, 240)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", 'B', 10); pdf.cell(0, 8, txt=" FLIGHT PREPARATION", ln=True, fill=True)
            pdf.set_font("Helvetica", size=9)
            pdf.cell(90, 7, txt=f"Date/Time: {self.current_results.get('time')}", border='B')
            pdf.cell(0, 7, txt=f"Commander: {self.ids.captain_input.text.upper()}", border='B', ln=True)
            pdf.cell(0, 7, txt=f"Prepared By: {self.ids.preparer_input.text.upper()}", border='B', ln=True); pdf.ln(5)

            pdf.set_font("Helvetica", 'B', 10); pdf.cell(0, 8, txt=" CABIN & CARGO DISTRIBUTION", ln=True, fill=True)
            pdf.set_font("Helvetica", size=9)
            for i in range(8):
                pdf.cell(45, 6, txt=f"{PAX_ROW_LABELS[i]}: {self.SEAT_TYPES[self.seat_states[i]][0]}", border=0)
                if i % 2 != 0: pdf.ln(6)
            pdf.cell(45, 6, txt=f"{PAX_ROW_LABELS[8]}: {self.SEAT_TYPES[self.seat_states[8]][0]}", border=0, ln=True)
            pdf.ln(2)
            pdf.set_font("Helvetica", 'B', 9)
            pdf.cell(0, 6, txt=f"FWD BAGGAGE: {self.current_results.get('fwd')} kg | AFT BAGGAGE: {self.current_results.get('aft')} kg", ln=True)
            pdf.cell(0, 6, txt=f"TKS FLUID: {self.current_results.get('tks')} kg", ln=True); pdf.ln(5)

            pdf.set_font("Helvetica", 'B', 10); pdf.cell(0, 8, txt=" FUEL PLANNING", ln=True, fill=True)
            pdf.set_font("Helvetica", size=9)
            pdf.cell(60, 7, txt=f"TAKEOFF FUEL: {self.current_results.get('fuel')} kg", border='B')
            pdf.cell(60, 7, txt=f"TRIP FUEL: {self.current_results.get('burn')} kg", border='B')
            pdf.cell(0, 7, txt=f"LANDING FUEL: {self.current_results.get('lnd_fuel')} kg", border='B', ln=True); pdf.ln(5)

            pdf.set_font("Helvetica", 'B', 10); pdf.cell(0, 8, txt=" FINAL WEIGHT & BALANCE SUMMARY", ln=True, fill=True)
            pdf.set_font("Helvetica", 'B', 9)
            pdf.cell(55, 8, txt="STATION", border=1, align='C')
            pdf.cell(45, 8, txt="MASS (kg)", border=1, align='C')
            pdf.cell(45, 8, txt="LIMIT (kg)", border=1, align='C')
            pdf.cell(0, 8, txt="CG (% MAC)", border=1, align='C', ln=True)
            
            pdf.set_font("Helvetica", size=9)
            pdf.cell(55, 8, txt="Zero Fuel Mass (MAX 3560)", border=1)
            pdf.cell(45, 8, txt=f"{self.current_results.get('zfm_m'):.1f} kg", border=1, align='R')
            pdf.cell(45, 8, txt=f"{MZFM_LIMIT} kg", border=1, align='R')
            pdf.cell(0, 8, txt=f"{self.current_results.get('zfm_mac'):.1f}", border=1, align='R', ln=True)
            
            pdf.cell(55, 8, txt="Take-off Mass (MAX 3680)", border=1)
            pdf.cell(45, 8, txt=f"{self.current_results.get('ramp_m'):.1f} kg", border=1, align='R')
            pdf.cell(45, 8, txt=f"{MTOM_LIMIT} kg", border=1, align='R')
            pdf.cell(0, 8, txt=f"{self.current_results.get('ramp_mac'):.1f}", border=1, align='R', ln=True)
            
            pdf.cell(55, 8, txt="Landing Mass (MAX 3630)", border=1)
            pdf.cell(45, 8, txt=f"{self.current_results.get('lnd_m'):.1f} kg", border=1, align='R')
            pdf.cell(45, 8, txt=f"{MLND_LIMIT} kg", border=1, align='R')
            pdf.cell(0, 8, txt=f"{self.current_results.get('lnd_mac'):.1f}", border=1, align='R', ln=True); pdf.ln(5)

            pdf.image(temp_plot_path, x=25, w=160)
            pdf.set_y(-25)
            pdf.set_font("Helvetica", 'I', 8)


            pdf.output(path)
            if os.path.exists(temp_plot_path): os.remove(temp_plot_path)
            self.ids.result_label.text = "PDF SAVED TO DOWNLOADS"
        except Exception as e:
            self.ids.result_label.text = f"EXPORT ERROR: {str(e)[:30]}"

    def reset_form(self):
        self.ids.captain_input.text = ""
        self.ids.preparer_input.text = ""
        self.ids.fwd_input.text = ""; self.ids.aft_input.text = ""
        self.ids.fuel_input.text = ""; self.ids.burn_input.text = ""
        self.ids.tks_input.text = ""; self.ids.pilot_toggle.state = 'normal'
        self.has_second_pilot = False; self.seat_states = [0] * 9; self.setup_seats(0)

class TecnamApp(App):
    def build(self):
        # This part pops up the "Allow access to files" window on your phone
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.MANAGE_EXTERNAL_STORAGE
            ])
            
        self.title = "G-CMCY Loadmaster"
        Builder.load_string(KV)
        root = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        root.add_widget(TecnamLayout())
        return root

if __name__ == "__main__":
    TecnamApp().run()