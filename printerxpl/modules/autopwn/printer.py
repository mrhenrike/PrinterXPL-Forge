"""printerxpl AutoPwn — printer segment. # authorized use only"""
from .base import SegmentAutoPwn
class PrinterAutoPwn(SegmentAutoPwn):
    def __init__(self, targets, **kw): super().__init__("printer", targets, **kw)
