'''
Created on Feb 20, 2015

@author: qurban.ali
'''
import nuke
import re
import os
import sys
import time
from datetime import datetime

from Qt.QtWidgets import QApplication, QMessageBox

import utilities.msgBox as msgBox
import utilities.appUsageApp as appUsageApp
import createArchive

reload(createArchive)

beauty = re.compile('beauty', re.I)
character = re.compile('char', re.I)
parent = QApplication.activeWindow()
__title__ = 'Render Write'


def getTime(seconds):
    tim = str(
        datetime.fromtimestamp(seconds)).split()[-1].split('.')[0].split(':')
    hour = int(tim[0])
    if hour > 12:
        hour = hour % 12
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


def getInputNodes(node):
    nodes = set()
    for dep in node.dependencies():
        nodes.add(dep)
        nodes.update(getInputNodes(dep))
    return list(nodes)


def render(*args):
    ''' get all selected nodes and render them using range determined from
    their network '''

    if not [node for node in nuke.selectedNodes() if node.Class() == 'Write']:
        msgBox.showMessage(parent,
                           title=__title__,
                           msg='No Write node found in the selection',
                           icon=QMessageBox.Information)
        return

    goodNodes = {}

    for writenode in nuke.selectedNodes():
        if writenode.Class() != 'Write':
            continue
        goodNodes[writenode.name()] = [
            writenode.firstFrame(),
            writenode.lastFrame()
        ]

    length = len(goodNodes)
    done = 1

    for goodNode in goodNodes.keys():
        createArchive.create(nuke.toNode(goodNode))

    print 'Starting render (%s nodes)' % str(length)
    for goodNode, value in goodNodes.items():
        seconds = time.time()
        filepath = nuke.toNode(goodNode).knob('file').getValue()
        basename = os.path.basename(filepath).split('.')[0]
        sys.stdout.write(
            str(done) + ' of ' + str(length) + ' ==> ' + str(goodNode) +
            ' (%s) ' % basename + ' Frame Range:(%s, %s) ' %
            (value[0], value[1]) + ' Start Time: ' + str(getTime(seconds)))
        flag = False
        try:
            nuke.execute(goodNode, value[0], value[1], continueOnError=True)
        except Exception as ex:
            flag = True
            if str(ex).startswith('Cancelled'):
                btn = msgBox.showMessage(
                    parent,
                    title=__title__,
                    msg='Could not render %s, %s' % (goodNode, str(ex)),
                    ques='Do you want to continue with the remaining nodes?',
                    icon=QMessageBox.Question,
                    btns=QMessageBox.Yes | QMessageBox.No)
                if btn == QMessageBox.No:
                    break
        done += 1
        seconds2 = time.time()
        m, s = divmod(seconds2 - seconds, 60)
        h, m = divmod(m, 60)
        sys.stdout.write(' - End Time: ' + str(getTime(seconds2)) +
                         " (%d:%02d:%02d) " % (h, m, s))
        print ' ==> Not rendered (%s)' % str(
            ex) if flag else ' ==> Rendered successfully'
    appUsageApp.updateDatabase('BatchRender')
