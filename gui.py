##############################
# Book order simulator
##############################

import sys
import wx
import time
import numpy as np


WIN_SIZE = (1024, 800)

def call_later(func):
   def func_wrapper(*args, **kwargs):
       return wx.CallAfter(func, *args, **kwargs)
   return func_wrapper

def format(p) :  
   p = float(p)
   return "%d %3.2f" %(p/1000, p - int(p/1000)*1000)

class LogWindow(wx.Frame):
   def __init__(self, parent):
      super(LogWindow, self).__init__(parent, size=(800, 600))
      self.init_ui()
      #self.Centre()
      self.Show()     

   def init_ui(self):

      panel = wx.Panel(self, -1)
      login_text = wx.StaticText(panel, -1, 'Username')
      password_text = wx.StaticText(panel, -1, 'Password')
      api_text = wx.StaticText(panel, -1, 'APIKey')
      epic_text = wx.StaticText(panel, -1, 'Epic')
      is_demo_text = wx.StaticText(panel, -1, 'Demo?')

      epics = ['IX.D.DAX.IMF.IP', # DAX
      ]

      self.login = wx.TextCtrl(panel, -1, '', )
      self.password = wx.TextCtrl(panel, -1, '',  style=wx.TE_PASSWORD)
      self.api = wx.TextCtrl(panel, -1, '',  )
      self.epic = wx.Choice(panel, -1, choices=epics)
      self.is_demo = wx.CheckBox(panel, -1, '', )

      connect_button = wx.Button(panel, 1, 'Connect',)
      disconnect_button = wx.Button(panel, 2, 'Exit', )
      
      panel_box = wx.BoxSizer(wx.VERTICAL)
      for (t, b) in [ (login_text, self.login), (password_text, self.password), 
                      (api_text, self.api), 
                      (epic_text, self.epic),
                      (is_demo_text, self.is_demo),
                      (connect_button, disconnect_button)]:
         box = wx.BoxSizer(wx.HORIZONTAL)
         box.Add(t, 1)
         box.Add(b, 1)
         panel_box.Add(box, wx.ALIGN_CENTER)

      panel_box.SetSizeHints(panel)
      panel.SetSizer(panel_box)
   
      connect_button.Bind(wx.EVT_BUTTON, self.connect)
      
   def connect(self, item):
      pass

class Window(wx.Frame):
  
    def __init__(self, parent,  title, pivots):
        super(Window, self).__init__(parent, title=title, 
                                      size=WIN_SIZE)
            
        self.init_ui()
        self.Centre()
        self.set_pivots(pivots)
        self.Show()     

        
    def init_ui(self):
        self.statusbar = self.CreateStatusBar()

        panel = wx.Panel(self, -1)

        button_size = wx.Size(100, 100)
        self.buy_button = wx.Button(panel, -1, size=button_size)
        self.sell_button = wx.Button(panel, -1, size=button_size)
        self.nb_pos = wx.StaticText(panel, -1, label="Nb Pos: ")
        self.balance = wx.StaticText(panel, -1, label="Balance: ")
        self.pnl = wx.StaticText(panel, -1, label="Daily pnl: ")
        self.pivots = [wx.StaticText(panel, -1, label=str(i)) for i in range(7)]
        
        widgets = [self.buy_button, self.sell_button, self.nb_pos, self.balance, self.pnl]
        widgets += self.pivots
        font1 = wx.Font(24, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Consolas')
        for w in widgets:
            w.SetFont(font1)
        
        self.position_list = wx.ListCtrl(panel, -1, style=wx.LC_REPORT)
        self.columns = [u'guaranteedStop', u'status', u'direction', u'limitLevel', u'level', u'affectedDeals', u'limitDistance', u'dealReference', u'dealStatus', u'dealId', u'reason', u'stopLevel', u'epic', u'stopDistance', u'expiry', u'size']
        map(lambda c: self.position_list.InsertColumn(*c), enumerate(self.columns))
        
        button_box = wx.BoxSizer(wx.HORIZONTAL)
        button_box.Add(self.buy_button, 1)
        button_box.Add(self.sell_button, 1)

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(button_box, 1, wx.EXPAND | wx.ALL, 10 )
        box.Add(self.nb_pos, 1, wx.ALIGN_CENTER)
        box.Add(self.balance, 1, wx.ALIGN_CENTER)
        box.Add(self.pnl, 1, wx.ALIGN_CENTER)
        for p in self.pivots:
            box.Add(p, 1, wx.ALIGN_CENTER)
        box.Add(self.position_list, 1, wx.EXPAND)
        
        box.SetSizeHints(panel)
        panel.SetSizer(box)
        self.update_balance()
        self.update_price(10000, 10000)
        
        self.total_pnl = 0
        self.history = {}

    @call_later
    def update_price(self, bid, ask):
        self.buy_button.SetLabel('Buy @ ' + format(bid))
        self.sell_button.SetLabel('Sell @ ' + format(ask))
        self.statusbar.SetStatusText("last updated: " + time.strftime("%H:%M:%S"))

    @call_later
    def update_balance(self, balance='NA', pnl='NA', nb_pos='NA'):
        self.nb_pos.SetLabel( " Total pos: %s" %  nb_pos)
        self.balance.SetLabel( "balance: %s, PNL: %s" % (balance, pnl))

    @call_later
    def add_position(self, pos):
        index = self.position_list.InsertStringItem(0, '')
        try:
           affectedDeals =pos[5]
           dealId = affectedDeals[0]['dealId']
           if self.history.has_key(dealId):
              pnl = pos[4] - self.history[dealId]
              if pos[2] == 'BUY': pnl = -pnl
              self.total_pnl += pnl
              self.pnl.SetLabel("Daily pnl: %.2f" % self.total_pnl)
           else:
              self.history[dealId] = pos[4]
        except :
           pass

        for i, p in enumerate(pos):
            self.position_list.SetStringItem(index, i, str(p))
    
    @call_later
    def set_pivots(self, pivots):
        labels = "R3 R2 R1 P S1 S2 S3".split()
        for i, p in enumerate(pivots[::-1]):
           p = format(p)
           self.pivots[i].SetLabel(labels[i] + ": " + p)
           color = (255, 0, 0) if i > 3 else (0, 255, 0) if i < 3  else (0, 0, 0)
           self.pivots[i].SetForegroundColour(color)

if __name__ == "__main__":
   app = wx.App()
   window = LogWindow(None)
   app.MainLoop()

