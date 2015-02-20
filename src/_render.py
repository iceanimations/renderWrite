'''
Created on Feb 20, 2015

@author: qurban.ali
'''
import nuke
import re
import msgBox
from PyQt4.QtGui import QApplication, QMessageBox

beauty = re.compile('beauty', re.I)
character = re.compile('char', re.I)
parent = QApplication.activeWindow()
__title__ = 'Render Write'

def render(*args):
    if not [node for node in nuke.selectedNodes() if node.Class() == 'Write']:
        msgBox.showMessage(parent, title=__title__,
                           msg='No Write node found in the selection',
                           icon=QMessageBox.Information)
        return
    badNodes = {}
    goodNodes = {}
    for writenode in nuke.selectedNodes():
        if writenode.Class() != 'Write':
            continue
    
        for node in nuke.selectedNodes():
            node.setSelected(False)
        
        writenode.setSelected(True)
        nuke.selectConnectedNodes()
        first = None
        last = None
        
        for readnode in nuke.selectedNodes('Read'):
            path = readnode.knob('file').getValue()
            if (beauty.search(path) and
                     character.search(path)):
                print writenode.name(), readnode.name()
                first=readnode.knob('first').getValue()
                last=readnode.knob('last').getValue()
                break
        if first is not None and last is not None:
            goodNodes[writenode.name()] = [int(first), int(last)]
        else:
            badNodes[writenode.name()] = 'Could not find frame range'
    if badNodes:
        detail = ''
        for nodeName, msg in badNodes.items():
            detail += nodeName +'\nReason: '+msg +'\n'
        btn = msgBox.showMessage(parent, title=__title__,
                                 msg='Could not find frame range for nodes',
                                 ques='Do you want to proceed anyway?',
                                 icon=QMessageBox.Information,
                                 details=detail,
                                 btns=QMessageBox.Yes|QMessageBox.No)
        if btn == QMessageBox.No:
            return
    for goodNode, value in goodNodes.items():
            nuke.render(goodNode, value[0], value[1])