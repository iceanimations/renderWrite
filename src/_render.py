'''
Created on Feb 20, 2015

@author: qurban.ali
'''
import nuke
import re
import os
import msgBox
from PyQt4.QtGui import QApplication, QMessageBox
import time
from datetime import datetime
import sys

beauty = re.compile('beauty', re.I)
character = re.compile('char', re.I)
parent = QApplication.activeWindow()
__title__ = 'Render Write'


def getTime(seconds):
    tim = str(datetime.fromtimestamp(seconds)).split()[-1].split('.')[0].split(':')
    hour = int(tim[0])
    if hour > 12:
        hour = hour%12
    elif hour == 0:
        hour = 12
    return ':'.join([str(hour), tim[1], tim[2]])

def mkdir(path):
    if not os.path.exists(path):
        parent = os.path.dirname(path)
        mkdir(parent)
        try:
            os.mkdir(path)
            return True
        except:
            return False
    elif os.path.isdir(path):
        return True
    return False

def render(*args):
    ''' get all selected nodes and render them using range determined from
    their network '''

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
                first=readnode.knob('first').getValue()
                last=readnode.knob('last').getValue()
                break

        if first is not None and last is not None:
            parent_dir = os.path.dirname(writenode.knob('file').getValue())
            if mkdir(parent_dir):
                goodNodes[writenode.name()] = [int(first), int(last)]
            else:
                badNodes[writenode.name()] = 'Could not create parent Directory ' + parent_dir
        else:
            badNodes[writenode.name()] = 'Could not find frame range'

    if badNodes:
        detail = ''
        for nodeName, msg in badNodes.items():
            detail += nodeName +'\nReason: '+msg +'\n'
        btn = msgBox.showMessage(parent, title=__title__,
                                 msg='Errors occurred while preparing rendering for some nodes',
                                 ques='Do you want to proceed anyway?',
                                 icon=QMessageBox.Information,
                                 details=detail,
                                 btns=QMessageBox.Yes|QMessageBox.No)
        if btn == QMessageBox.No:
            return

    length = len(goodNodes)
    done = 1
    print 'Starting render (%s nodes)'%str(length), goodNodes
    for goodNode, value in goodNodes.items():
        seconds = time.time()
        filepath = nuke.toNode(goodNode).knob('file').getValue()
        basename = os.path.basename(filepath).split('.')[0]
        sys.stdout.write(str(done) +' of '+ str(length) +' ==> '+ str(goodNode)
                + ' (%s) '%basename+' Start: '+ str(getTime(seconds)))
        flag = False
        try:
            nuke.render(goodNode, value[0], value[1], continueOnError=True)
        except RuntimeError:
            flag = True
            btn = msgBox.showMessage(parent, title=__title__,
                                     msg='Could not render "%s" due to some error or user interruption'%goodNode,
                                     ques='Do you want to continue with the remaining nodes?',
                                     icon=QMessageBox.Question,
                                     btns=QMessageBox.Yes|QMessageBox.No)
            if btn == QMessageBox.No:
                break
        done += 1
        seconds2 = time.time()
        m, s = divmod(seconds2 - seconds, 60)
        h, m = divmod(m, 60)
        sys.stdout.write(' - End: '+ str(getTime(seconds2)) +" (%d:%02d:%02d) "%(h, m, s))
        status = ' ==> Not rendered' if flag else ' ==> Rendered successfully'
        print status
